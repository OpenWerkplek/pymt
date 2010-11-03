'''
Window: Create a GL Window

For windowing system, we try to use the best windowing system available for
your system. Actually, theses libraries are handled :

    * PyGame (wrapper around SDL)
    * GLUT (last solution, really buggy :/)

'''

__all__ = ('WindowBase', 'Window')

from pymt.core import core_select_lib
from pymt.config import pymt_config
from pymt.logger import Logger
from pymt.base import setWindow, touch_event_listeners
from pymt.modules import pymt_modules
from pymt.event import EventDispatcher

class WindowBase(EventDispatcher):
    '''WindowBase is a abstract window widget, for any window implementation.

    .. warning::

        The parameters are not working in normal case. Because at import, PyMT
        create a default OpenGL window, to add the ability to use OpenGL
        directives, texture creation.. before creating MTWindow.
        If you don't like this behavior, you can include before the very first
        import of PyMT ::

            import os
            os.environ['PYMT_SHADOW'] = '0'
            from pymt import *

        This will forbid PyMT to create the default window !


    :Parameters:
        `fps`: int, default to 0
            Maximum FPS allowed. If 0, fps will be not limited
        `fullscreen`: bool
            Make window as fullscreen
        `width`: int
            Width of window
        `height`: int
            Height of window
        `vsync`: bool
            Vsync window
    '''

    __instance = None
    __initialized = False

    def __new__(cls, **kwargs):
        if cls.__instance is None:
            cls.__instance = EventDispatcher.__new__(cls)
        return cls.__instance

    def __init__(self, **kwargs):

        kwargs.setdefault('force', False)
        kwargs.setdefault('config', None)
        kwargs.setdefault('show_fps', False)

        # don't init window 2 times,
        # except if force is specified
        if self.__initialized and not kwargs.get('force'):
            return

        super(WindowBase, self).__init__()

        # init privates
        self._modifiers = []
        self._size = (0, 0)
        self._rotation = 0

        # event subsystem
        self.register_event_type('on_flip')
        self.register_event_type('on_rotate')
        self.register_event_type('on_draw')
        self.register_event_type('on_update')
        self.register_event_type('on_resize')
        self.register_event_type('on_close')
        self.register_event_type('on_touch_down')
        self.register_event_type('on_touch_move')
        self.register_event_type('on_touch_up')
        self.register_event_type('on_mouse_down')
        self.register_event_type('on_mouse_move')
        self.register_event_type('on_mouse_up')
        self.register_event_type('on_keyboard')
        self.register_event_type('on_key_down')
        self.register_event_type('on_key_up')

        # set out window as the main pymt window
        setWindow(self)

        #self.children = SafeList()
        #self.parent = self
        #self.visible = True

        # add view
        if 'view' in kwargs:
            self.add_widget(kwargs.get('view'))

        # get window params, user options before config option
        params = {}

        if 'fullscreen' in kwargs:
            params['fullscreen'] = kwargs.get('fullscreen')
        else:
            params['fullscreen'] = pymt_config.get('graphics', 'fullscreen')
            if params['fullscreen'] not in ('auto', 'fake'):
                params['fullscreen'] = params['fullscreen'].lower() in \
                    ('true', '1', 'yes', 'yup')

        if 'width' in kwargs:
            params['width'] = kwargs.get('width')
        else:
            params['width'] = pymt_config.getint('graphics', 'width')

        if 'height' in kwargs:
            params['height'] = kwargs.get('height')
        else:
            params['height'] = pymt_config.getint('graphics', 'height')

        if 'vsync' in kwargs:
            params['vsync'] = kwargs.get('vsync')
        else:
            params['vsync'] = pymt_config.getint('graphics', 'vsync')

        if 'fps' in kwargs:
            params['fps'] = kwargs.get('fps')
        else:
            params['fps'] = pymt_config.getint('graphics', 'fps')

        if 'rotation' in kwargs:
            params['rotation'] = kwargs.get('rotation')
        else:
            params['rotation'] = pymt_config.getint('graphics', 'rotation')

        params['position'] = pymt_config.get(
            'graphics', 'position', 'auto')
        if 'top' in kwargs:
            params['position'] = 'custom'
            params['top'] = kwargs.get('top')
        else:
            params['top'] = pymt_config.getint('graphics', 'top')

        if 'left' in kwargs:
            params['position'] = 'custom'
            params['left'] = kwargs.get('left')
        else:
            params['left'] = pymt_config.getint('graphics', 'left')

        # show fps if asked
        self.show_fps = kwargs.get('show_fps')
        if pymt_config.getboolean('pymt', 'show_fps'):
            self.show_fps = True

        # configure the window
        self.create_window(params)

        # attach modules + listener event
        pymt_modules.register_window(self)
        touch_event_listeners.append(self)

        # mark as initialized
        self.__initialized = True

    def toggle_fullscreen(self):
        '''Toggle fullscreen on window'''
        pass

    def close(self):
        '''Close the window'''
        pass

    def create_window(self, params):
        '''Will create the main window and configure it'''
        pass

    def on_flip(self):
        '''Flip between buffers (event)'''
        self.flip()

    def flip(self):
        '''Flip between buffers'''
        pass

    def dispatch_events(self):
        '''Dispatch all events from windows'''
        pass

    def _get_modifiers(self):
        return self._modifiers
    modifiers = property(_get_modifiers)

    def _get_size(self):
        r = self._rotation
        w, h = self._size
        if r == 0 or r == 180:
            return w, h
        return h, w
    def _set_size(self, size):
        if super(WindowBase, self)._set_size(size):
            Logger.debug('Window: Resize window to %s' % str(self.size))
            self.dispatch_event('on_resize', *size)
            return True
        return False
    size = property(_get_size, _set_size,
        doc='''Rotated size of the window''')

    # make some property read-only
    @property
    def width(self):
        '''Rotated window width'''
        r = self._rotation
        if r == 0 or r == 180:
            return self._size[0]
        return self._size[1]
    @property
    def height(self):
        '''Rotated window height'''
        r = self._rotation
        if r == 0 or r == 180:
            return self._size[1]
        return self._size[0]
    @property
    def center(self):
        '''Rotated window center'''
        return self.width / 2., self.height / 2.

    def add_widget(self, w):
        '''Add a widget on window'''
        self.children.append(w)
        w.parent = self

    def remove_widget(self, w):
        '''Remove a widget from window'''
        if not w in self.children:
            return
        self.children.remove(w)
        w.parent = None

    def clear(self):
        '''Clear the window with background color'''
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def draw(self):
        '''Draw the window background'''
        self.clear()

    def to_widget(self, x, y, initial=True, relative=False):
        return (x, y)

    def to_window(self, x, y, initial=True, relative=False):
        return (x, y)

    def get_root_window(self):
        return self

    def get_parent_window(self):
        return self

    def get_parent_layout(self):
        return None

    def on_update(self):
        '''Event called when window are update the widget tree.
        (Usually before on_draw call.)
        '''
        for w in self.children[:]:
            w.dispatch_event('on_update')

    def on_draw(self):
        '''Event called when window we are drawing window.
        This function are cleaning the buffer with bg-color css,
        and call children drawing + show fps timer on demand'''

        # draw our window
        self.draw()

        # then, draw childrens
        for w in self.children[:]:
            w.dispatch_event('on_draw')

    def on_touch_down(self, touch):
        '''Event called when a touch is down'''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in reversed(self.children[:]):
            if w.dispatch_event('on_touch_down', touch):
                return True

    def on_touch_move(self, touch):
        '''Event called when a touch move'''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in reversed(self.children[:]):
            if w.dispatch_event('on_touch_move', touch):
                return True

    def on_touch_up(self, touch):
        '''Event called when a touch up'''
        w, h = self.system_size
        touch.scale_for_screen(w, h, rotation=self._rotation)
        for w in reversed(self.children[:]):
            if w.dispatch_event('on_touch_up', touch):
                return True

    def on_resize(self, width, height):
        '''Event called when the window is resized'''
        self.update_viewport()

    def update_viewport(self):
        width, height = self.system_size
        w2 = width / 2.
        h2 = height / 2.

        # prepare the viewport
        glViewport(0, 0, width, height)

        # set the projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-w2, w2, -h2, h2, .1, 1000)
        glScalef(5000, 5000, 1)

        # use the rotated size.
        width, height = self.size
        w2 = width / 2.
        h2 = height / 2.
        glTranslatef(-w2, -h2, -500)

        # set the model view
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(w2, h2, 0)
        glRotatef(self._rotation, 0, 0, 1)
        glTranslatef(-w2, -h2, 0)

        # update window size
        for w in self.children:
            shw, shh = w.size_hint
            if shw and shh:
                w.size = shw * width, shh * height
            elif shw:
                w.width = shw * width
            elif shh:
                w.height = shh * height

    def _get_rotation(self):
        return self._rotation
    def _set_rotation(self, x):
        x = int(x % 360)
        if x == self._rotation:
            return
        if x not in (0, 90, 180, 270):
            raise ValueError('can rotate only 0,90,180,270 degrees')
        self._rotation = x
        self.dispatch_event('on_resize', *self.size)
        self.dispatch_event('on_rotate', x)
    rotation = property(_get_rotation, _set_rotation,
            'Get/set the window content rotation. Can be one of '
            '0, 90, 180, 270 degrees.')

    @property
    def system_size(self):
        '''Real size of the window, without taking care of the rotation
        '''
        return self._size

    def on_rotate(self, rotation):
        '''Event called when the screen have been rotated
        '''
        pass

    def on_close(self, *largs):
        '''Event called when the window is closed'''
        pymt_modules.unregister_window(self)
        if self in touch_event_listeners[:]:
            touch_event_listeners.remove(self)

    def on_mouse_down(self, x, y, button, modifiers):
        '''Event called when mouse is in action (press/release)'''
        pass

    def on_mouse_move(self, x, y, modifiers):
        '''Event called when mouse is moving, with buttons pressed'''
        pass

    def on_mouse_up(self, x, y, button, modifiers):
        '''Event called when mouse is moving, with buttons pressed'''
        pass

    def on_keyboard(self, key, scancode=None, unicode=None):
        '''Event called when keyboard is in action

        .. warning::
            Some providers can skip `scancode` or `unicode` !!
        '''
        pass

    def on_key_down(self, key, scancode=None, unicode=None):
        '''Event called when a key is down (same arguments as on_keyboard)'''
        pass

    def on_key_up(self, key, scancode=None, unicode=None):
        '''Event called when a key is up (same arguments as on_keyboard)'''
        pass


# Load the appropriate provider
Window = core_select_lib('window', (
    ('pygame', 'window_pygame', 'WindowPygame'),
))

