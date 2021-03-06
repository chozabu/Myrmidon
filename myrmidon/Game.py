""" 
Myrmidon
Copyright (c) 2010 Fiona Burrows

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

---------------------

An open source, actor based framework for fast game development for Python.

This contains the primary Game object from where you manipulate
and interact with the application.
"""

import sys, os, math, copy, inspect, time
from myrmidon.BaseEntity import BaseEntity
from myrmidon.ModuleLoader import ModuleLoader
from myrmidon.consts import *


@ModuleLoader
class Game(object):

    ######################################################################################
    # USER API 
    ######################################################################################
    
    # Enabling debugging will allow invoking of PUDB with the F11 key
    debug = False
    
    # Set to true at run-time and Myrmidon will not create a screen,
    # nor will it accept input or execute any entities in a loop.
    # No backend engines are initialised.
    # Any entity objects you create will not integrate their generator
    # unless you run Entity._iterate_generator manually.
    test_mode = False  # API

    # The framerate the game should be capped at.
    target_fps = 30

    # The framerate the game is currently running at. Read-only.
    current_fps = 0
    
    # The screen resolution the game should start at
    screen_resolution = 1024,768
    
    lowest_resolution = 800,600
    
    # Set to True to have the game begin full-screen
    full_screen = False
    
    device_scale = 1.0

    # Backwards compatibility flags
    screen_size_adjustment_compatability_mode = False
    
    # The number of frames that have been executed, for counting reasons. Read-only.
    current_frame = 0
    
    # Floats that represent how long it took for the previous frame to execute the
    # process logic and to render respectivly, in seconds. Read-only.
    frame_execution_time = 0.0
    frame_render_time = 0.0
        
    @classmethod
    def define_engine(cls, window=None, gfx=None, input=None, audio=None):
        """ 
        Use this before creating any entities to redefine which engine backends to use.
        """
        if window:
            cls.engine_def['window'] = window
        if gfx:
            cls.engine_def['gfx'] = gfx
        if input:
            cls.engine_def['input'] = input
        if audio:
            cls.engine_def['audio'] = audio

    @classmethod
    def define_engine_plugins(cls, window=[], gfx=[], input=[], audio=[]):
        """ 
        Use this before creating any entities to specify which engine plugins you require,
        if any.
        Pass in lists of strings of plugin names.
        """
        cls.engine_plugin_def['window'] = window
        cls.engine_plugin_def['gfx'] = gfx
        cls.engine_plugin_def['input'] = input
        cls.engine_plugin_def['audio'] = audio
    
    @classmethod
    def change_resolution(cls, resolution):
        """ 
        Changes the screen resolution at runtime.
        """
        cls.screen_resolution = resolution
        cls.engine['window'].change_resolution(resolution)
        cls.engine['gfx'].change_resolution(resolution)
    
    @classmethod
    def destroy_entities(cls, target, tree=False):
        """Kills Entity objects, stopping them from executing, displaying and
        irreversibly destroying them.

        Keyword arguments:
        -- target: A number of different types can be passed in as the target of this method -
          * A single Entity instance, in this case only that one Entity will be destroyed.
          * An Entity class type (not instanced object, will also match subclasses)
          * A string containing the name of the class type searching for.
        -- tree: If True then all children of all matched Entities (and their children
          etc) will be destroyed too. (default False)
        """
        entity_list = cls.get_entities(target, tree=tree)
        for entity in entity_list:
            if (not entity in cls.entity_list) or (entity in cls.entities_to_remove):
                continue
            entity.on_exit()
            Game.entities_to_remove.append(entity)

    @classmethod
    def stop_entities_executing(cls, target, tree=False):
        """Stops Entities executing code. Can be woke up again with start_entities_executing
        or toggle_entities_executing.

        Keyword arguments:
        -- target: A number of different types can be passed in as the target of this method -
          * A single Entity instance, in this case only that one Entity will be stopped.
          * An Entity class type (not instanced object, will also match subclasses)
          * A string containing the name of the class type searching for.
        -- tree: If True then all children of all matched Entities (and their children
          etc) will be stopped too. (default False)
        """
        entity_list = cls.get_entities(target, tree=tree)
        for entity in entity_list:
            entity._executing = False

    @classmethod
    def start_entities_executing(cls, target, tree=False):
        """Starts Entities executing code if previously stopped.

        Keyword arguments:
        -- target: A number of different types can be passed in as the target of this method -
          * A single Entity instance, in this case only that one Entity will be stopped.
          * An Entity class type (not instanced object, will also match subclasses)
          * A string containing the name of the class type searching for.
        -- tree: If True then all children of all matched Entities (and their children
          etc) will be started too. (default False)
        """
        entity_list = cls.get_entities(target, tree=tree)
        for entity in entity_list:
            entity._executing = True

    @classmethod
    def toggle_entities_executing(cls, target, tree=False):
        """Toggle the execution of Entities. If started they will be stopped
        and vise-versa.

        Keyword arguments:
        -- target: A number of different types can be passed in as the target of this method -
          * A single Entity instance, in this case only that one Entity will be stopped.
          * An Entity class type (not instanced object, will also match subclasses)
          * A string containing the name of the class type searching for.
        -- tree: If True then all children of all matched Entities (and their children
          etc) will be toggled too. (default False)
        """
        entity_list = cls.get_entities(target, tree=tree)
        for entity in entity_list:
            entity._executing = not entity._executing

    @classmethod
    def hide_entities(cls, target, tree = False):
        """Stops Entities rendering. Can be set to draw again with show_entities or
        or toggle_entities_display.

        Keyword arguments:
        -- target: A number of different types can be passed in as the target of this method -
          * A single Entity instance, in this case only that one Entity will be stopped.
          * An Entity class type (not instanced object, will also match subclasses)
          * A string containing the name of the class type searching for.
        -- tree: If True then all children of all matched Entities (and their children
          etc) will be hidden too. (default False)
        """
        entity_list = cls.get_entities(target, tree=tree)
        for entity in entity_list:
            entity.drawing = False

    @classmethod
    def show_entities(cls, target, tree = False):
        """Starts Entities rendering code if previously stopped.

        Keyword arguments:
        -- target: A number of different types can be passed in as the target of this method -
          * A single Entity instance, in this case only that one Entity will be stopped.
          * An Entity class type (not instanced object, will also match subclasses)
          * A string containing the name of the class type searching for.
        -- tree: If True then all children of all matched Entities (and their children
          etc) will be shown too. (default False)
        """
        entity_list = cls.get_entities(target, tree=tree)
        for entity in entity_list:
            entity.drawing = True

    @classmethod
    def toggle_entities_display(cls, target, tree=False):
        """Toggle the rendering of Entities. If hidden they will be shown
        and vise-versa.

        Keyword arguments:
        -- target: A number of different types can be passed in as the target of this method -
          * A single Entity instance, in this case only that one Entity will be stopped.
          * An Entity class type (not instanced object, will also match subclasses)
          * A string containing the name of the class type searching for.
        -- tree: If True then all children of all matched Entities (and their children
          etc) will be toggled too. (default False)
        """
        entity_list = cls.get_entities(target, tree=tree)
        for entity in entity_list:
            entity.drawing = not entity.drawing

    @classmethod
    def get_entities(cls, target, tree = False):
        """This method returns a list of all Entities matching a type searched for.

        Keyword arguments:
        -- target: A number of different types can be passed in as the target of this method -
          * A single Entity instance, in this case only that one Entity will be destroyed.
          * An Entity class type (not instanced object, will also match subclasses)
          * A string containing the name of the class type searching for.
        -- tree: If True then all childen of matched Entities  will be added too. (default False)
        """
        found_entity_list = []
        # We've entered a specific type as a string
        if isinstance(target, str):
            for obj in cls.entity_list:
                if obj.__class__.__name__ == target:
                    cls.add_entity_to_list(obj, found_entity_list, tree=tree)

        # We've passed in a class type directly
        elif isinstance(target, type):
            for obj in cls.entity_list:
                if isinstance(obj, target):
                    cls.add_entity_to_list(obj, found_entity_list, tree=tree)

        # We've passed in an Entity instance
        elif isinstance(target, BaseEntity):
            cls.add_entity_to_list(target, found_entity_list, tree=tree)

        return found_entity_list

    @classmethod
    def keyboard_key_down(cls, key_code):
        """ 
        Ask if a key is currently being pressed.
        Pass in key codes that is relevant to your chosen input backend.
        """
        if not cls.engine['input']:
            raise MyrmidonError("Input backend not initialised.")
        return cls.engine['input'].keyboard_key_down(key_code)

    @classmethod
    def keyboard_key_released(cls, key_code):
        """ 
        Ask if a key has just been released last frame.
        Pass in key codes that is relevant to your chosen input backend.
        """
        if not cls.engine['input']:
            raise MyrmidonError("Input backend not initialised.")
        return cls.engine['input'].keyboard_key_released(key_code)

    @classmethod
    def mouse(cls):
        """Gives access to an Entity object that represents the mouse.
        """
        return cls.engine['input'].mouse

    @classmethod
    def load_image(cls, image = None, sequence = False, width = None, height = None, **kwargs):
        """Creates and returns an Image object that we can then attach to an Entity's image member
        to display graphics.
        A particular graphics engine may also have their own specific arguments not documented here.

        Keyword arguments:
        image -- The filesystem path to the filename that the image is contained in. Typically this can
          also be a pointer to already loaded image data if the gfx in-use supports such behaviour. (for
          instance, engines using PyGame to load images can be given a PyGame surface directly.) (Required)
        sequence -- Denotes if the image being loaded contains a series of images as frames. (default False)
        width -- If we have a sequence of images, this denotes the width of each frame. (default None)
        height -- The height of a frame in a sequence image, if not supplied this will default to
          the width. (default None)
        """
        return cls.engine['gfx'].Image(image, sequence, width, height, **kwargs)

    @classmethod
    def load_font(cls, font = None, size = 20, **kwargs):
        """Creates and returns a Font object that we give to the write_text method to specify how to render
        text. You can also dynamically change the font attribute of Text objects.
        A particular window engine may also have their own specific arguments not documented here.

        Keyword arguments:
        font -- The filesystem path to the filename that the font is contained in. Typically this can
          also be a pointer to an already loaded font if the engine in-use supports this behaviour. (For
          instance, eungines using Pygame for font loading can be given a pygame.font.Font object directly.)
          If None is supplied then the default internal font will be used if applicable. (default None)
        size -- The size of the text that we want to display. What this value actually relates to is dependant
          on the font loading engine used. (default 20)
        """
        return cls.engine['window'].Font(font, size, **kwargs)

    @classmethod
    def load_audio(cls, audio):
        """Creates and returns an Audio object that we can manipulate directly to play sounds.
        A particular audio engine may also have their own specific arguments not documented here.

        Keyword arguments:
        audio -- The filesystem path to the file that the sound is contained at. Typically this can
          also be a pointer to an already loaded audio object if the engine in-use supports this behaviour.
          (For instance, eungines using Pygame for audio can be given a pygame.mixer.Sound object directly.)
          (default None)
        """
        return cls.engine['audio'].Audio(audio)

    @classmethod
    def write_text(cls, x, y, font, alignment = 0, text = "", antialias = True):
        return cls.engine['gfx'].Text(font, x, y, alignment, text, antialias = True)

    @classmethod
    def create_rectangle(cls, x, y, width, height, colour=(1.0, 1.0, 1.0), line_width=0):
        """ 
        Creates and returns a rectangle entity at the given position, with the given width and height.
        :param x: Initial x coordinate
        :param y: Initial y coordinate
        :param width: The width of the rectangle in pixels
        :param height: The height of the rectangle in pixels
        :param colour: Optional 3-tuple specifying the RGB colour. Defaults to white.
        :param line_width: If zero, rectangle is filled, if positive rectangle is unfilled using this line thickness.
                           Defaults to zero.
        :return: A rectangle object
        """
        return cls.engine['gfx'].Rectangle(x, y, width, height, colour, line_width)

    @classmethod
    def create_ellipse(cls, x, y, width, height, colour=(1.0, 1.0, 1.0), line_width=0, start_angle=0, end_angle=360):
        """ 
        Creates and returns an ellipse entity at the given position and with the given width and height
        :param x: Initial x coordinate
        :param y: Initial y coordinate
        :param width: The width of the bounding box that the ellipse should fit
        :param height: The height of the bounding box that the ellipse should fit
        :param colour: Optional 3-tuple specifying the RGB colour. Defaults to white
        :param line_width: If zero, ellipse is filled. If positive, ellipse is unfilled using this line thickness.
        :param start_angle: The angle at which to start in order to draw only a segment of the ellipse. Defaults to 0
        :param end_angle: The angle at which to end in order to draw only a segment of the ellipse. Defaults to 360
        :return: An ellipse object
        """
        return cls.engine['gfx'].Ellipse(x, y, width, height, colour, line_width, start_angle, end_angle)

    @classmethod
    def create_line(cls, x, y, points, colour=(1.0, 1.0, 1.0), line_width=1.0, closed=False):
        """ 
        Creates and returns a line entity at the given position and with the given points. A line entity consists of one
        or more lines connected together to form a single shape. This shape is centred at the specified x and y
        coordinates
        :param x: Initial x position of the shape
        :param y: Initial y position of the shape
        :param points: List of coordinate 2-tuples defining a line or polyline. Coordinates are relative to what will be
                       the top-left corner of the entity, and should be >= 0. The width and height of the shape will be
                       defined by the bounding box around all the points in the shape.
        :param colour: Optional 3-tuple specifying the RGB colour. Defaults to white.
        :param line_width: The thickness of line to use. Defaults to 1.0
        :param closed: If True, the last line will be connected to the first in a loop
        :return: A line object
        """
        return cls.engine['gfx'].Line(x, y, points, colour, line_width, closed)

    @classmethod
    def get_distance(cls, pointa, pointb):
        return math.sqrt((math.pow((pointb[1] - pointa[1]), 2) + math.pow((pointb[0] - pointa[0]), 2)))

    @classmethod
    def get_distance_squared(cls, pointa, pointb):
        return (math.pow((pointb[1] - pointa[1]), 2) + math.pow((pointb[0] - pointa[0]), 2))

    @classmethod
    def move_forward(cls, pos, distance, angle):
        pos2 = [0.0,0.0]

        pos2[0] = pos[0] + distance * math.cos(math.radians(angle))
        pos2[1] = pos[1] + distance * math.sin(math.radians(angle))

        return pos2

    @classmethod
    def angle_between_points(cls, pointa, pointb):
        """ 
        Take two tuples each containing coordinates between two points and
        returns the angle between those in degrees
        """
        return cls.normalise_angle(math.degrees(math.atan2(pointb[1] - pointa[1], pointb[0] - pointa[0])))

    @classmethod
    def normalise_angle(cls, angle):
        """ 
        Returns an equivalent angle value between 0 and 360
        """
        return angle % 360.0

    @classmethod
    def angle_difference(cls, start_angle, end_angle, skip_normalise = False):
        """ 
        Returns the angle to turn by to get from start_angle to end_angle.
        The sign of the result indicates the direction in which to turn.
        """
        if not skip_normalise:
            start_angle = cls.normalise_angle(start_angle)
            end_angle = cls.normalise_angle(end_angle)

        difference = end_angle - start_angle
        if difference > 180.0:
            difference -= 360.0
        if difference < -180.0:
            difference += 360.0

        return difference

    @classmethod
    def near_angle(cls, curr_angle, targ_angle, increment, leeway = 0):
        """ 
        Returns an angle which has been moved from 'curr_angle' closer to
        'targ_angle' by 'increment'. increment should always be positive, as
        angle will be rotated in the direction resulting in the shortest
        distance to the target angle.
        leeway specifies an acceptable distance from the target to accept,
        allowing you to specify a segment to reach rather than a specific angle.
        The angle is returned unchanged if within the target segment.
        """
        # Normalise curr_angle
        curr_angle = cls.normalise_angle(curr_angle)

        # Normalise targ_angle
        targ_angle = cls.normalise_angle(targ_angle)

        # calculate difference
        difference = cls.angle_difference(curr_angle, targ_angle, skip_normalise = True)

        # do increment
        if math.fabs(difference) <= leeway:
            return curr_angle
        elif math.fabs(difference) < increment:
            return targ_angle
        else:
            dir = difference / math.fabs(difference)
            return curr_angle + (increment * dir)

    @classmethod
    def rotate_point(cls, x, y, rotation):
        """Rotates a point by the given number of degrees about the origin.

        Keyword arguments:
        -- x:  First coordinate part of the point.
        -- y:  Second coordinate part of the point.
        -- rotation:  The amount to rotate by in degrees."""
        rotation = math.radians(rotation)
        return (math.cos(rotation) * x - math.sin(rotation) * y,
                math.sin(rotation) * x + math.cos(rotation) * y)

    @classmethod
    def rotate_point_about_point(cls, x, y, rotation, rotate_about_x, rotate_about_y):
        """Similar to rotate_point but allows specification of a separate point
        in space to rotate around.

        Keyword arguments:
        -- x:  First coordinate part of the point.
        -- y:  Second coordinate part of the point.
        -- rotation:  The amount to rotate by in degrees.
        -- rotate_about_x: First coordinate part of the point to rotate around.
        -- rotate_about_y: Second coordinate part of the point to rotate around."""
        p = cls.rotate_point(x - rotate_about_x, y - rotate_about_y, rotation)
        return p[0] + rotate_about_x, p[1] + rotate_about_y

    @classmethod
    def point_in_rectangle(cls, point, rectangle_origin, rectangle_size):
        """Returns True/False if a point is within a rectangle shape.

        Keyword arguments:
        -- point: Tuple containing the coordinates of the point.
        -- rectangle_origin: Tuple containing the top left corner of the rectangle.
        -- rectangle_size: Tuple containing the width and height of the rectangle.
        """
        return (point[0] > rectangle_origin[0] and
                point[0] < (rectangle_origin[0] + rectangle_size[0]) and
                point[1] > rectangle_origin[1] and
                point[1] < (rectangle_origin[1] + rectangle_size[1]))

    @classmethod
    def screen_overlay_on(cls, fade_speed=None, colour_from=(0.0, 0.0, 0.0, 0.0), colour_to=(0.0, 0.0, 0.0, 1.0), 
                          blocking=False, pos=(0, 0), size=None, z=-1024, callback=None):
        """Turns on and fades in a coloured overlay on the screen, usually this
        is used to create full screen fading effects.
        If called when the overlay is fading it will silently return instead
        of starting another fade effect.

        Keyword arguments:
        -- fade_speed: Specify how fast the screen should fade in by passing in
         a timer generator returned by timer_* methods.
         Example:
         Passing in Game.timer_ticks(60) as the fade_speed argument will cause the
         fade to last for 60 game ticks.
         If None, the overlay will take 30 ticks to fade in. (default None)
        -- colour_from: RGBA colour values between 0 and 1 that specify what colour to
         fade the screen from. A linear interpolation will be performed from these
         values to the ones specified by the colour_to parameter.
         By default this is a fully transparent black. (default (0.0, 0.0, 0.0, 1.0))
        -- colour_to: RGBA colour values between 0 and 1 that specify what colour to
         fade the screen to. By default this is a fully opaque black.
         (default (0.0, 0.0, 0.0, 1.0))
        -- blocking: If a fade is set to be blocking then no Entities will execute
         their code while it the fade is happening. As soon as the fade is complete
         Entities will continue to execute again. (Even if the screen is then hidden).
         Entities will continue to draw if they are being blocked.
         (default False)
        -- pos: Where on the screen the overlay will be drawn from in pixels. By default
         this is the top left corner of the screen. (default (0, 0))
        -- size: How big the overlay should be in pixels, if None is passed in then it will
         default to the entire screen resolution. (default None)
        -- z: The Z layer that the overlay should be drawn at. (default -1024)
        -- callback: Sometimes you want some arbitrary code to run after a fade has completed,
         you can pass a callable into this parameter to achieve that. As soon as the current fade
         operation has completed it will be called.
        """
        if not cls.screen_overlay is None:
            return

        # Set default args
        if fade_speed is None:
            fade_speed = cls.timer_ticks(30)
        if pos is None:
            pos = (0, 0)
        pos = (pos[0] - Game.global_x_pos_adjust, pos[1] - Game.global_y_pos_adjust)
        if size is None:
            size = cls.screen_resolution[0] * cls.device_scale, cls.screen_resolution[1] * cls.device_scale

        from myrmidon.ScreenOverlay import ScreenOverlay
        cls.screen_overlay = ScreenOverlay(colour_from, colour_to, blocking, pos, size, z, callback)
        cls.screen_overlay.fade_from_to(fade_speed)
        if blocking:
            cls.disable_entity_execution = True

    @classmethod
    def screen_overlay_off(cls, fade_speed = None, blocking = False, callback = None):
        """Any overlay that is currently on and completed will be faded out
        using this method. It will do nothing if there is not currently
        an overlay on the screen and finished it's fading.
        It uses the colour_to and colour_from parameters previously
        given to screen_overlay_on to fade between, interolating in the opposite
        direction.
        Once it has finished fading it will be automatically destroyed.

        Keyword arguments:
        -- fade_speed: Specify how fast the screen should fade in by passing in
         a timer generator returned by timer_* methods.
         Example:
         Passing in Game.timer_ticks(60) as the fade_speed argument will cause the
         fade to last for 60 game ticks.
         If None, the overlay will take 30 ticks to fade in. (default None)
        -- blocking: If a fade is set to be blocking then no Entities will execute
         their code while it the fade is happening. As soon as the fade is complete
         Entities will continue to execute again. (Even if the screen is then hidden).
         Entities will continue to draw if they are being blocked.
         (default False)
        -- callback: Sometimes you want some arbitrary code to run after a fade has completed,
         you can pass a callable into this parameter to achieve that. As soon as the current fade
         operation has completed it will be called. (default None)
        """
        if cls.screen_overlay is None:
            return
        if fade_speed is None:
            fade_speed = cls.timer_ticks(30)
        cls.screen_overlay.blocking = blocking
        cls.screen_overlay.callback = callback
        cls.screen_overlay.fade_to_from(fade_speed)
        if cls.screen_overlay.blocking:
            cls.disable_entity_execution = True

    @classmethod
    def is_screen_overlay_fading(cls):
        """Returns a boolean denoting if any screen overlay currently
        displayed is doing it's fade animation. It will return False
        if there is no overlay and as soon as the fading animation is
        finished, even if the overlay is still being displayed.
        """
        if cls.screen_overlay is None:
            return False
        return cls.screen_overlay.fading

    @classmethod
    def is_screen_overlay_on(cls):
        """Returns a boolean denoting if a screen overlay is
        currently on the screen. It will be True even if the overlay
        is in the middle of a fade animation.
        """
        return not cls.screen_overlay is None

    @classmethod
    def rgba_to_colour(cls, r=255, g=255, b=255, a=255):
        """Converts an RGBA colour value to a float based colour value that
        myrmidon understands.
        Returns a tuple containing RGBA colour values between 0 and 1.

        Keyword arguments:
        -- r: Red component value (default 255)
        -- g: Green component value (default 255)
        -- b: Blue component value (default 255)
        -- a: Alpha component value (default 255)
        """
        return cls.engine['gfx'].rgb_to_colour((r, g, b, a))

    @classmethod
    def rgb_to_colour(cls, r=255, g=255, b=255):
        """Converts an RGB colour value to a float based colour value that
        myrmidon understands.
        Returns a tuple containing RGB colour values between 0 and 1.

        Keyword arguments:
        -- r: Red component value (default 255)
        -- g: Green component value (default 255)
        -- b: Blue component value (default 255)
        """
        vals = cls.rgba_to_colour(r, g, b)
        return vals[0], vals[1], vals[2]

    @classmethod
    def hsva_to_colour(cls, hue=0, sat=1.0, val=1.0, alpha=255):
        """Converts an HSVA colour value to a float-based RGBA colour value that
        myrmidon understands.
        Returns a 4-tuple containing RGBA colour values between 0 and 1
        :param hue: The hue value in degrees between 0 and 360
        :param sat: The saturation between 0 and 1
        :param val: The brightness value between 0 and 1
        :param alpha: The alpha value between 0 and 255
        :returns The colour as a 4-tuple"""
        chroma = val * sat
        sixth = (hue % 360) / 60.0
        othcomp = chroma * (1.0 - abs((sixth % 2) - 1.0))
        if 0 <= sixth < 1:
            r, g, b = chroma, othcomp, 0
        elif 1 <= sixth < 2:
            r, g, b = othcomp, chroma, 0
        elif 2 <= sixth < 3:
            r, g, b = 0, chroma, othcomp
        elif 3 <= sixth < 4:
            r, g, b = 0, othcomp, chroma
        elif 4 <= sixth < 5:
            r, g, b = othcomp, 0, chroma
        elif 5 <= sixth < 6:
            r, g, b = chroma, 0, othcomp
        else:
            r, g, b = 0, 0, 0
        r += val - chroma
        g += val - chroma
        b += val - chroma
        return cls.rgba_to_colour(int(r*255), int(g*255), int(b*255), alpha)

    @classmethod
    def hsv_to_colour(cls, hue=0, sat=1.0, val=1.0):
        """Converts an HSV colour value to a float-based RGB colour value that
        myrmidon understands.
        Returns a 3-tuple containing RGB colour values between 0 and 1
        :param hue: The hue value in degrees between 0 and 360
        :param sat: The saturation between 0 and 1
        :param val: The brightness value between 0 and 1
        :returns The colour as a 3-tuple"""
        vals = cls.hsva_to_colour(hue, sat, val)
        return vals[0], vals[1], vals[2]

    # American spelling aliases
    rgba_to_color = rgba_to_colour
    rgb_to_color = rgb_to_colour
    hsva_to_color = hsva_to_colour
    hsv_to_color = hsv_to_colour

    @classmethod
    def lerp(cls, start, end, amount):
        """Performs a linear interpolation by giving the value
        of percentage between the specified start and end values.

        For instance:
        lerp(0.0, 100.0, .5)
        Would return 50.0.

        Keyword arguments:
        -- start: The start value of the interpolation as a float.
        -- end: The end value of the interpolation as a float.
        -- amount: What position between the start and end points
         to return, given as a float value between 0 and 1.
         """
        return (start + amount * (end - start))

    @classmethod
    def slerp(cls, start, end, amount):
        """Does the same as lerp except maps the value to a smooth curve
        as opposed to a straight line.

        Keyword arguments:
        -- start: The start value of the interpolation as a float.
        -- end: The end value of the interpolation as a float.
        -- amount: What position between the start and end points
         to return, given as a float value between 0 and 1.
        """
        # Perform the curve adjustment
        amount = ((amount) * (amount) * (3 - 2 * (amount)))
        return (start + amount * (end - start))

    @classmethod
    def timer_ticks(cls, ticks_to_wait):
        """Returns a generator that iterates as many times as the value
        given, is designed to be used in Entity code as a timer that counts
        ticks.
        The generator returns how many times it's returned to that point and
        the total number of ticks, as floats in a two-part tuple.

        Example usage:

        for frame, total in Game.timer_ticks(10):
            yield

        Within an Entity's execute method, this would cause the Entity to
        wait 10 ticks.

        Keyword arguments:
        -- ticks_to_wait: The number of times the generator should iterate.
        """
        ticks_waited = 0
        while ticks_waited < ticks_to_wait:
            ticks_waited += 1
            yield float(ticks_waited),float(ticks_to_wait)

    @classmethod
    def timer_ticks_unit(cls, ticks_to_wait):
        """Returns a generator that iterates as many times as the value given, similar
        to 'timer_ticks'.
        The generator returns float values increasing from 0.0 to 1.0, including 1.0 but
        not 0.0.
        """
        for frame, total in cls.timer_ticks(ticks_to_wait):
            yield frame / total

    @classmethod
    def call_in_future(cls, function, frames_in_future):
        """Will call the passed function the number of frames in the future
        passed in. For instance, passing '30' for frames_in_future will cause Myrmidon
        to automatically call the function after 30 frames of execution."""
        time = cls.current_frame + frames_in_future
        if not time in cls.scheduled_on_frame:
            cls.scheduled_on_frame[time] = []
        cls.scheduled_on_frame[time].append(function)

        
    
    ######################################################################################
    # INTERNAL
    ######################################################################################

    # Engine related
    started = False 

    engine_def = {
        "window" : "pygame",
        "gfx" : "opengl",
        "input" : "pygame",
        "audio" : "pygame"
        }
    engine_plugin_def = {
        "window" : [],
        "gfx" : [],
        "input" : [],
        "audio" : []
        }
    engine = {
        "window" : None,
        "gfx" : None,
        "input" : None,
        "audio" : None
        }

    # Module related members
    _module_list = []
    modules_enabled = ()
    modules_loaded_for = []

    # Entity related
    first_registered_entity = None
    entity_list = []
    entity_draw_list = []
    entities_to_remove = []
    remember_current_entity_executing = []
    current_entity_executing = None
    entity_priority_dirty = True
    did_collision_check = False
    
    # Global flag disables all entity execution, does not apply to any screen overlay entities.
    disable_entity_execution = False

    # Set to an overlay Entity if one has been created
    screen_overlay = None

    # Designed to be set by the window engine, if it's set to True, we imply that the device
    # we're running on is a mobile device of some kind. (Will also be True for tablets.)
    is_phone = False

    # A dictionary of frame numbers to functions that need to be called when the game hits
    # those frames. They're called after every entity has finished executing on the relevant frame.
    scheduled_on_frame = {}

    @classmethod
    def init_engines(cls):
        # Attempt to dynamically import the required engines
        try:
            for backend_name in ['window', 'gfx', 'input', 'audio']:
                backend_module = __import__(
                    "myrmidon.engine.%s.%s.engine" % (backend_name, cls.engine_def[backend_name]),
                    globals(),
                    locals(),
                    ['Myrmidon_Backend'],
                    0
                    )
                cls.engine[backend_name] = backend_module.Myrmidon_Backend()

        except ImportError as detail:
            print("Error importing a backend engine.", detail)
            sys.exit()

        # Test mode uses dummy engines
        if cls.test_mode:
            from .backend_dummy import MyrmidonWindowDummy, MyrmidonGfxDummy, MyrmidonInputDummy, MyrmidonAudioDummy
            cls.engine['window'] = MyrmidonWindowDummy()
            cls.engine['gfx'] = MyrmidonGfxDummy()
            cls.engine['input'] = MyrmidonInputDummy()
            cls.engine['audio'] = MyrmidonAudioDummy()
            return

    @classmethod
    def load_engine_plugins(cls, engine_object, backend_name):
        # Import plugin modules and create them
        try:
            engine_object.plugins = {}
            if len(cls.engine_plugin_def[backend_name]):
                for plugin_name in  cls.engine_plugin_def[backend_name]:
                    plugin_module = __import__(
                        "engine.%s.%s.plugins.%s" % (backend_name, cls.engine_def[backend_name], plugin_name),
                        globals(),
                        locals(),
                        ['Myrmidon_Backend'],
                        -1
                        )
                    engine_object.plugins[plugin_name] = plugin_module.Myrmidon_Engine_Plugin(engine_object)

        except ImportError as detail:
            print("Error importing a backend engine plugin.", detail)
            sys.exit()

    @classmethod
    def start_game(cls):
        """ 
        Called by entities if a game is not yet started.
        It initialises engines.
        """
        # Start up the backends
        cls.init_engines()
        cls.clock = cls.engine['window'].Clock()

    @classmethod
    def run_game(cls):
        """ 
        Called by entities if a game is not yet started.
        Is responsible for the main loop.
        """
        # No execution of anything if in tests mode.
        if cls.test_mode:
            return

        # Deal with creating modules
        for x in cls._module_list:
            x._module_setup(cls)

        cls.engine['window'].set_window_loop(cls.app_loop_callback, cls.target_fps)
        cls.engine['window'].open_window()

    @classmethod
    def app_loop_callback(cls, dt):
        # Start frame timer
        frame_timer = time.time()
        
        cls.engine['window'].app_loop_tick()

        # If we need to register something
        if cls.first_registered_entity:
            cls.entity_register(cls.first_registered_entity)
            cls.first_registered_entity = None

        # Reorder Entities by execution priority if necessary
        if cls.entity_priority_dirty == True:
            cls.entity_list.sort(
                reverse=True,
                key=lambda object:
                object.priority if hasattr(object, "priority") else 0
                )
            cls.entity_priority_dirty = False

        # If we have an input engine enabled we pass off to it
        # to manage and process input events.
        if cls.engine['input']:
            cls.engine['input'].process_input()

        if cls.debug and cls.keyboard_key_released(K_F11):
            from pudb import set_trace; set_trace()

        # For each entity in priority order we iterate their
        # generators executing their code
        if not cls.disable_entity_execution:
            for entity in cls.entity_list:
                cls.current_entity_executing = entity
                entity._iterate_generator()
                if cls.disable_entity_execution:
                    if not cls.screen_overlay is None:
                        cls.current_entity_executing = cls.screen_overlay
                        cls.screen_overlay._iterate_generator()
                    break
        else:
            if not cls.screen_overlay is None:
                cls.current_entity_executing = cls.screen_overlay
                cls.screen_overlay._iterate_generator()

        # Handled scheduled timer functions
        cls.current_frame += 1
        if cls.current_frame in cls.scheduled_on_frame:
            for function in cls.scheduled_on_frame[cls.current_frame]:
                function()
            del(cls.scheduled_on_frame[cls.current_frame])

        # If we have marked any entities for removal we do that here
        for x in cls.entities_to_remove:
            if x in cls.entity_list:
                if x.next_sibling:
                    x.next_sibling.prev_sibling = None
                if x.prev_sibling:
                    x.prev_sibling.next_sibling = None
                if x.parent and x.parent.child is x:
                    x.parent.child = None
                x.parent = None
                cls.engine['gfx'].remove_entity(x)
                cls.entity_list.remove(x)
                cls.entity_draw_list.remove(x)
        cls.entities_to_remove = [] 

        # Save how long it took to execute
        cls.frame_execution_time = time.time() - frame_timer

        # Pass off to the gfx engine to display entities
        cls.engine['gfx'].update_screen_pre()
        cls.engine['gfx'].draw_entities(cls.entity_draw_list)
        cls.engine['gfx'].update_screen_post()

        # Save how long it took to render
        cls.frame_render_time = time.time() - cls.frame_execution_time - frame_timer

        # Hack - we assume a window backend will *either* return a non-zero fps value from the clock object
        # *or* have provided a non-zero time delta value, depending on how the main loop is handled
        clock_fps = int(cls.clock.get_fps())
        cls.current_fps = clock_fps if dt == 0 else 1.0/dt

        # Wait for next frame, hitting a particular fps
        cls.clock.tick(cls.target_fps)
    
    @classmethod
    def entity_register(cls, entity):
        """ 
        Registers an entity with Myrmidon so it will be executed.
        """
        cls.entity_list.append(entity)
        cls.entity_draw_list.append(entity)
        cls.engine['gfx'].register_entity(entity)
        cls.entity_priority_dirty = True

        # Handle relationships
        if cls.current_entity_executing != None:
            entity.parent = cls.current_entity_executing

            if not entity.parent.child == None:
                entity.parent.child.prev_sibling = entity

            entity.next_sibling = entity.parent.child
            entity.parent.child = entity
    
    @classmethod
    def add_entity_to_list(cls, entity, entity_list, tree = False):
        """Used by the get_entities method to add a single Entity object to
        a list, if it doesn't already exist in the list, along with a tree of
        children if applicable.

        Keyword arguments:
        -- entity: An Entity obj to add to the given list.
        -- entity_list: The list to add to.
        -- tree: If we want to also add all the children of the Entity to the
          list. (default False)
        """
        if not entity in entity_list:
            entity_list.append(entity)

        if tree:
            next_child = entity.child
            while next_child != None:
                if not next_child in entity_list:
                    cls.add_entity_to_list(next_child, entity_list, tree = tree)
                next_child = next_child.next_sibling

    @classmethod
    def collision_rectangle_to_rectangle(cls, rectangle_a, rectangle_b):
        """ 
        Uses the separating axis theorem to check collisions between two
        Entities. Both must have COLLISION_TYPE_RECTANGLE set as their collision type.
        Returns True/False on collision.

        Keyword arguments:
        -- rectangle_a: The first Entity we are checking.
        -- rectangle_b: The Entity we are checking the first one against.
        """
        # retrieve loctaions of box corners
        check_object_a = rectangle_a.collision_rectangle_calculate_corners()
        check_object_b = rectangle_b.collision_rectangle_calculate_corners()

        # Step 1 is calculating the 4 axis of our two objects
        # we will use them check the collisions
        axis = [(0,0), (0,0), (0,0), (0,0)]

        axis[0] = (check_object_a['ur'][0] - check_object_a['ul'][0],
                   check_object_a['ur'][1] - check_object_a['ul'][1])

        axis[1] = (check_object_a['ur'][0] - check_object_a['lr'][0],
                   check_object_a['ur'][1] - check_object_a['lr'][1])

        axis[2] = (check_object_b['ul'][0] - check_object_b['ll'][0],
                   check_object_b['ul'][1] - check_object_b['ll'][1])

        axis[3] = (check_object_b['ul'][0] - check_object_b['ur'][0],
                   check_object_b['ul'][1] - check_object_b['ur'][1])

        # We will need to determine a collision for each of the 4 axis
        # If any of the axis do ~not~ collide then we determine that no
        # collision has occured.
        for single_axis in axis:
            # Step 2 is projecting the vectors of each corner of each rectangle
            # on to the axis. This is to determine the min/max projected vectors
            # of each rectangle.
            corner_vector_projection = {rectangle_a: dict(check_object_a), rectangle_b: dict(check_object_b)}
            rectangle_bounds = {rectangle_a: {'min' : None, 'max' : None}, rectangle_b: {'min' : None, 'max' : None}}

            for object_ in corner_vector_projection:
                for corner_name in corner_vector_projection[object_]:
                    projection = (
                        (
                            (corner_vector_projection[object_][corner_name][0] * single_axis[0]) 
                                + (corner_vector_projection[object_][corner_name][1] * single_axis[1])
                        ) / (
                            (single_axis[0] * single_axis[0]) + (single_axis[1] * single_axis[1])
                        )
                    )
                    corner_vector_projection[object_][corner_name] = ((projection * single_axis[0]) * single_axis[0]) \
                        + ((projection * single_axis[1]) * single_axis[1])

                    # Step 3 is working out what the min and max location of each corner
                    # projected on the axis is for each rectangle.
                    if rectangle_bounds[object_]['min'] is None \
                            or corner_vector_projection[object_][corner_name] < rectangle_bounds[object_]['min']:
                        rectangle_bounds[object_]['min'] = corner_vector_projection[object_][corner_name]

                    if rectangle_bounds[object_]['max'] is None \
                            or corner_vector_projection[object_][corner_name] > rectangle_bounds[object_]['max']:
                        rectangle_bounds[object_]['max'] = corner_vector_projection[object_][corner_name]

            # Step 4 is determining if the min and max corner projections of each rectangle on the axis overlap
            # If they don't then we can conclude that no collision has occured.
            if not (rectangle_bounds[rectangle_b]['min'] <= rectangle_bounds[rectangle_a]['max'] \
                    and rectangle_bounds[rectangle_b]['max'] >= rectangle_bounds[rectangle_a]['min']):
                return False

        # If we have got this far then we can assume that a collision has occured.
        return True

    @classmethod
    def collision_point_to_rectangle(cls, point, rectangle):
        """ 
        Checks the collision between an Entity with it's type as COLLISION_TYPE_POINT
        against one set as COLLISION_TYPE_RECTANGLE
        Returns True/False on collision.

        Keyword arguments:
        -- point: The Entity that is a point.
        -- rectangle: The Entity this is a rectangle.
        """
        # Get all usable values
        check_object_a = point.collision_point_calculate_point()
        check_object_b = rectangle.collision_rectangle_calculate_corners()
        check_object_b_size = rectangle.collision_rectangle_size()

        # rotate the point by -rectangle_angle around the centre of the rectangle
        rotated_point = Game.rotate_point_about_point(
            check_object_a[0],
            check_object_a[1],
            -rectangle.rotation,
            rectangle.x,
            rectangle.y
            )

        # Check that point is within the rectangle
        return Game.point_in_rectangle(rotated_point, check_object_b['ul'], check_object_b_size)

    @classmethod
    def collision_circle_to_rectangle(cls, circle, rectangle):
        """ 
        Checks the collision between an Entity with it's type as COLLISION_TYPE_CIRCLE
        against one set as COLLISION_TYPE_RECTANGLE
        Returns True/False on collision.

        Keyword arguments:
        -- circle: The Entity that is a circle.
        -- rectangle: The Entity this is a rectangle.
        """
        check_object_a = circle
        check_object_b = rectangle
        check_object_a_radius = check_object_a.collision_circle_calculate_radius()
        check_object_b_corners = check_object_b.collision_rectangle_calculate_corners()
        check_object_b_size = check_object_b.collision_rectangle_size()

        # rotate the cicle by -rectangle_angle around the centre of the rectangle
        rotated_ciricle = Game.rotate_point_about_point(
            check_object_a.x,
            check_object_a.y,
            -check_object_b.rotation,
            check_object_b.x,
            check_object_b.y
            )

        half_width = check_object_b_size[0] / 2
        half_height = check_object_b_size[1] / 2

        circle_distance = (abs(rotated_ciricle[0] - check_object_b.x), abs(rotated_ciricle[1] - check_object_b.y))

        if circle_distance[0] > (half_width + check_object_a_radius) or \
           circle_distance[1] > (half_height + check_object_a_radius):
            return False

        if circle_distance[0] <= half_width or \
           circle_distance[1] <= half_height:
            return True

        corner_distance_sq = ((circle_distance[0] - half_width) ** 2) + ((circle_distance[1] - half_height) ** 2)

        return (corner_distance_sq <= (check_object_a_radius**2))

    @classmethod
    def collision_circle_to_circle(cls, circle_a, circle_b):
        """ 
        Checks the collision between two Entities of type as COLLISION_TYPE_CIRCLE.
        Returns True/False on collision.

        Keyword arguments:
        -- circle_a: The first Entity.
        -- circle_b: The Entity we are checking against.
        """
        check_object_a = circle_a
        check_object_b = circle_b
        check_object_a_radius = check_object_a.collision_circle_calculate_radius()
        check_object_b_radius = check_object_b.collision_circle_calculate_radius()

        # Outside of each others radius
        if check_object_a.get_distance_squared((check_object_b.x, check_object_b.y)) > (check_object_a_radius + check_object_b_radius)**2:
            return False

        return True

    @classmethod
    def collision_point_to_circle(cls, point, circle):
        """ 
        Checks the collision between an Entity with it's type as COLLISION_TYPE_POINT
        against one set as COLLISION_TYPE_CIRCLE
        Returns True/False on collision.

        Keyword arguments:
        -- point: The Entity that is a point.
        -- circle: The Entity this is a circle.
        """
        check_object_a = point
        check_object_b = circle
        check_object_a_point = check_object_a.collision_point_calculate_point()
        check_object_b_radius = check_object_b.collision_circle_calculate_radius()

        # Outside of each others radius
        if cls.get_distance(check_object_a_point, (check_object_b.x,check_object_b.y)) > check_object_b_radius:
            return False

        return True

    @classmethod
    def collision_point_to_point(cls, point_a, point_b):
        """ 
        Checks collision between two Entities with their type as COLLISION_TYPE_POINT.
        Practically useless but here for completion.
        Returns True/False on collision.

        Keyword arguments:
        -- point_a: The first Entity.
        -- point_b: The Entity we are checking against.
        """
        point_a = point_a.collision_point_calculate_point()
        point_b = point_b.collision_point_calculate_point()
        return True if point_a[0] == point_b[0] and point_a[1] == point_b[1] else False


# Define the collision function lookups so we entities know which one to call
# depending on the types of Entities it is comparing.
# (We can't create this  function map until the class has been defined so we must
# do it out of the class definition here.)
Game.collision_methods = {
        (COLLISION_TYPE_RECTANGLE, COLLISION_TYPE_RECTANGLE) : Game.collision_rectangle_to_rectangle,
        (COLLISION_TYPE_POINT, COLLISION_TYPE_RECTANGLE) : Game.collision_point_to_rectangle,
        (COLLISION_TYPE_RECTANGLE, COLLISION_TYPE_POINT) : Game.collision_point_to_rectangle,
        (COLLISION_TYPE_CIRCLE, COLLISION_TYPE_RECTANGLE) : Game.collision_circle_to_rectangle,
        (COLLISION_TYPE_RECTANGLE, COLLISION_TYPE_CIRCLE) : Game.collision_circle_to_rectangle,
        (COLLISION_TYPE_CIRCLE, COLLISION_TYPE_CIRCLE) : Game.collision_circle_to_circle,
        (COLLISION_TYPE_POINT, COLLISION_TYPE_CIRCLE) : Game.collision_point_to_circle,
        (COLLISION_TYPE_CIRCLE, COLLISION_TYPE_POINT) : Game.collision_point_to_circle,
        (COLLISION_TYPE_POINT, COLLISION_TYPE_POINT) : Game.collision_point_to_point
        }


class MyrmidonError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
