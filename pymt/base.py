'''
Base: Main event loop, provider creation, window management...
'''

__all__ = (
    'EventLoop', 'Window',
    'runTouchApp', 'stopTouchApp',
    'getCurrentTouches',
)

import pymt
import sys
import os
from pymt.config import Config
from pymt.logger import Logger
from pymt.exceptions import ExceptionManager
from pymt.clock import Clock
from pymt.input import TouchFactory, pymt_postproc_modules

# private vars
EventLoop               = None
Window                  = None

def getCurrentTouches():
    '''Return the list of all current touches
    '''
    return touch_list

class EventLoopBase(object):
    '''Main event loop. This loop handle update of input + dispatch event
    '''
    def __init__(self):
        super(EventLoopBase, self).__init__()
        self.quit = False
        self.input_events = []
        self.postproc_modules = []
        self.status = 'idle'
        self.input_providers = []
        self.event_listeners = []

    def add_input_provider(self, provider):
        '''Add a new input provider to listen for touch event
        '''
        if not provider in self.input_providers:
            self.input_providers.append(provider)

    def remove_input_provider(self, provider):
        '''Remove an input provider
        '''
        if provider in self.input_providers:
            self.input_providers.remove(provider)

    def add_event_listener(self, listener):
        '''Add a new event listener for getting touch event
        '''
        if not listener in self.event_listeners:
            self.event_listeners.append(listener)

    def remove_event_listener(self, listener):
        '''Remove a event listener from the list
        '''
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)

    def start(self):
        '''Must be call only one time before run().
        This start all configured input providers.'''
        self.status = 'started'
        for provider in self.input_providers:
            provider.start()

    def close(self):
        '''Exit from the main loop, and stop all configured
        input providers.'''
        self.quit = True
        self.stop()
        self.status = 'closed'

    def stop(self):
        '''Stop all input providers'''
        #stop in reverse order that we started them!! (liek push pop),
        #very important becasue e.g. wm_touch and WM_PEN both store
        #old window proc and teh restore, if order is messed big problem
        #happens, crashing badly without error
        for provider in reversed(self.input_providers):
            provider.stop()
        self.status = 'stopped'

    def add_postproc_module(self, mod):
        '''Add a postproc input module (DoubleTap, RetainTouch are default)'''
        self.postproc_modules.append(mod)

    def remove_postproc_module(self, mod):
        '''Remove a postproc module'''
        if mod in self.postproc_modules:
            self.postproc_modules.remove(mod)

    def post_dispatch_input(self, event, touch):
        '''This function is called by dispatch_input() when we want to dispatch
        a input event. The event is dispatched into all listeners, and if
        grabbed, it's dispatched through grabbed widgets'''
        # update available list
        if event == 'down':
            touch_list.append(touch)
        elif event == 'up':
            if touch in touch_list:
                touch_list.remove(touch)

        # dispatch to listeners
        if not touch.grab_exclusive_class:
            for listener in self.event_listeners:
                if event == 'down':
                    listener.dispatch_event('on_touch_down', touch)
                elif event == 'move':
                    listener.dispatch_event('on_touch_move', touch)
                elif event == 'up':
                    listener.dispatch_event('on_touch_up', touch)

        # dispatch grabbed touch
        touch.grab_state = True
        for _wid in touch.grab_list[:]:

            # it's a weakref, call it!
            wid = _wid()
            if wid is None:
                # object is gone, stop.
                touch.grab_list.remove(_wid)
                continue

            root_window = wid.get_root_window()
            if wid != root_window and root_window is not None:
                touch.push()
                w, h = root_window.system_size
                touch.scale_for_screen(w, h, rotation=root_window.rotation)
                parent = wid.parent
                # and do to_local until the widget
                try:
                    if parent:
                        touch.apply_transform_2d(parent.to_widget)
                    else:
                        touch.apply_transform_2d(wid.to_widget)
                        touch.apply_transform_2d(wid.to_parent)
                except AttributeError:
                    # when using innerwindow, an app have grab the touch
                    # but app is removed. the touch can't access
                    # to one of the parent. (ie, self.parent will be None)
                    # and BAM the bug happen.
                    touch.pop()
                    continue

            touch.grab_current = wid

            if event == 'down':
                # don't dispatch again touch in on_touch_down
                # a down event are nearly uniq here.
                # wid.dispatch_event('on_touch_down', touch)
                pass
            elif event == 'move':
                wid.dispatch_event('on_touch_move', touch)
            elif event == 'up':
                wid.dispatch_event('on_touch_up', touch)

            touch.grab_current = None

            if wid != root_window and root_window is not None:
                touch.pop()
        touch.grab_state = False

    def _dispatch_input(self, event, touch):
        ev = (event, touch)
        # remove the save event for the touch if exist
        if ev in self.input_events[:]:
            self.input_events.remove(ev)
        self.input_events.append(ev)

    def dispatch_input(self):
        '''Called by idle() to read events from input providers,
        pass event to postproc, and dispatch final events'''
        # first, aquire input events
        for provider in self.input_providers:
            provider.update(dispatch_fn=self._dispatch_input)

        # execute post-processing modules
        for mod in self.postproc_modules:
            self.input_events = mod.process(events=self.input_events)

        # real dispatch input
        for event, touch in self.input_events:
            self.post_dispatch_input(event=event, touch=touch)

        self.input_events = []

    def idle(self):
        '''This function is called every frames. By default :
        * it "tick" the clock to the next frame
        * read all input and dispatch event
        * dispatch on_update + on_draw + on_flip on window
        '''
        # update dt
        Clock.tick()

        # read and dispatch input from providers
        self.dispatch_input()

        if pymt_window:
            pymt_window.dispatch_events()
            pymt_window.dispatch_event('on_update')
            pymt_window.dispatch_event('on_draw')
            pymt_window.dispatch_event('on_flip')

        # don't loop if we don't have listeners !
        if len(self.event_listeners) == 0:
            self.exit()
            return False

        return self.quit

    def run(self):
        '''Main loop'''
        while not self.quit:
            self.idle()
        self.exit()

    def exit(self):
        '''Close the main loop, and close the window'''
        self.close()
        if pymt_window:
            pymt_window.close()

#: EventLoop instance
EventLoop = EventLoopBase()

def _run_mainloop():
    '''If user haven't create a window, this is the executed mainloop'''
    while True:
        try:
            EventLoop.run()
            stopTouchApp()
            break
        except BaseException, inst:
            # use exception manager first
            r = ExceptionManager.handle_exception(inst)
            if r == ExceptionManager.RAISE:
                stopTouchApp()
                raise
            else:
                pass


def runTouchApp(widget=None, slave=False):
    '''Static main function that starts the application loop.
    You got some magic things, if you are using argument like this :

    :Parameters:
        `<empty>`
            To make dispatching work, you need at least one
            input listener. If not, application will leave.
            (MTWindow act as an input listener)

        `widget`
            If you pass only a widget, a MTWindow will be created,
            and your widget will be added on the window as the root
            widget.

        `slave`
            No event dispatching are done. This will be your job.

        `widget + slave`
            No event dispatching are done. This will be your job, but
            we are trying to get the window (must be created by you before),
            and add the widget on it. Very usefull for embedding PyMT
            in another toolkit. (like Qt, check pymt-designed)

    '''

    # Ok, we got one widget, and we are not in slave mode
    # so, user don't create the window, let's create it for him !
    ### Not needed, since we always create window ?!
    #if not slave and widget:
    #    global pymt_window
    #    from ui.window import MTWindow
    #    pymt_window = MTWindow()

    # Instance all configured input
    for key, value in Config.items('input'):
        Logger.debug('Base: Create provider from %s' % (str(value)))

        # split value
        args = str(value).split(',', 1)
        if len(args) == 1:
            args.append('')
        provider_id, args = args
        provider = TouchFactory.get(provider_id)
        if provider is None:
            Logger.warning('Base: Unknown <%s> provider' % \
                                str(provider_id))
            continue

        # create provider
        p = provider(key, args)
        if p:
            EventLoop.add_input_provider(p)

    # add postproc modules
    for mod in pymt_postproc_modules.values():
        EventLoop.add_postproc_module(mod)

    # add main widget
    if widget and getWindow():
        getWindow().add_widget(widget)

    # start event loop
    Logger.info('Base: Start application main loop')
    EventLoop.start()

    # we are in a slave mode, don't do dispatching.
    if slave:
        return

    # in non-slave mode, they are 2 issues
    #
    # 1. if user created a window, call the mainloop from window.
    #    This is due to glut, it need to be called with
    #    glutMainLoop(). Only FreeGLUT got a gluMainLoopEvent().
    #    So, we are executing the dispatching function inside
    #    a redisplay event.
    #
    # 2. if no window is created, we are dispatching event lopp
    #    ourself (previous behavior.)
    #
    try:
        if pymt_window is None:
            _run_mainloop()
        else:
            pymt_window.mainloop()
    finally:
        stopTouchApp()

def stopTouchApp():
    '''Stop the current application by leaving the main loop'''
    if EventLoop is None:
        return
    if EventLoop.status != 'started':
        return
    Logger.info('Base: Leaving application in progress...')
    EventLoop.close()
