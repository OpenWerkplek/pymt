'''
TouchTip: A simple animated hint system for interacting with multi-touch tables.
'''

from __future__ import with_statement

__all__ = ['MTTouchTip']

import pyglet
from ..factory import MTWidgetFactory
from widget import MTWidget
from animatedgif import MTAnimatedGif
from ...utils import curry
import os
import pymt

iconPath = os.path.join(pymt.pymt_data_dir, 'icons', 'touchtips', '')

class MTTouchTip(MTWidget):
    
    def __init__(self, **kwargs):
        super(MTTouchTip, self).__init__(**kwargs)
        
        self.tips = []
        self.clock = pyglet.clock.Clock()
        
        #Load all of our necessary images.
        pinch_1 = pyglet.image.load(iconPath+"pinch_1.png")
        pinch_2 = pyglet.image.load(iconPath+"pinch_2.png")
        pinch_3 = pyglet.image.load(iconPath+"pinch_3.png")
        self.pinch_seq = [pinch_1, pinch_2, pinch_3, pinch_3, pinch_3, pinch_2, pinch_1, pinch_1, pinch_1]
        
        tap_1 = pyglet.image.load(iconPath+"tap_1.png")
        tap_2 = pyglet.image.load(iconPath+"tap_2.png")
        self.tap_seq = [tap_1, tap_1, tap_2, tap_2, tap_2, tap_2]
        
    
    def attach(self, obj, type, delay=0.0, rotation=0.0, offset=(0,0)):
        '''Ataches a TouchTip to an existing object (must be, at some level, derived from MTWidget)
       
           :Parameters:
               `obj` : MTWidget-derived object
                   The object that the touchtip will be attached to. If the object is moved on the screen, the touchtip will move as well.
               `type` : string
                   Type of hint to give. Options are currently 'tap' or 'pinch'
               `delay` : float, default to 0.0
                   The length of time before the TouchTip will be displayed by the object. If the requirements (see below) are all met before this time is reached, then the TouchTip will never be displayed.
                   This time is in seconds.
               `rotation` : float, default to 0.0
                   Set the rotation (in degrees) of the TouchTip.
               `offset` : tuple of two integers, default to (0, 0)
                   Set the offset of the touchtip from the normal position (close to the center) of the attached object. Useful for precise positioning on an individual basis.
            
            A note on requirements:
                The following requirements are present for each of the following hint types before the hint is considered "complete" and will disappear:
                
                "tap": touch_down
                "pinch": touch_down, resize (this is meant to be used with MTScatterWidget objects)
            '''
        
        tip = MTWidget()
        
        tip.target = obj
        
        if(type == "pinch"):
            tip.anim = MTAnimatedGif(sequence = self.pinch_seq, delay=0.2)
            tip.target.push_handlers(on_touch_down=curry(self.handle_touch_event, tip, "touch_down"))
            tip.target.push_handlers(on_resize=curry(self.handle_event, tip, "resize"))
            tip.requirements = ['touch_down', 'resize']
        
        if(type == "tap"):
            tip.anim = MTAnimatedGif(sequence = self.tap_seq, delay=0.2)
            tip.target.push_handlers(on_touch_down=curry(self.handle_touch_event, tip, "touch_down"))
            tip.requirements = ['touch_down']
        
        tip.offset = offset
        tip.size = tip.anim.size
        tip.rotation = rotation
        tip.origsize = tip.size
        tip.shown = False
        tip.opacity = 0
        tip.delay = delay
        tip.add_animation('show','opacity', 120, 1.0/60, 2.0) 
        self.tips.append(tip)
        self.add_widget(tip)
    
    def handle_event(*largs):
        requirement = largs[2]
        tip = largs[1]
        if requirement in tip.requirements:
            tip.requirements.remove(requirement)
    
    def handle_touch_event(self, tip, requirement, touch):
        if tip.target.collide_point(touch.x, touch.y):
            if requirement in tip.requirements:
                tip.requirements.remove(requirement)
    
    def on_draw(self):
        
        self.bring_to_front()
        
        dt = self.clock.tick()
        deletetips = []
        
        for tip in self.tips:
            
            #Track the object the tip is assigned to.
            
            #Determine our scale based on the size of the object.
            scale_x = float(tip.target.size[0])/float(tip.origsize[0])
            scale_y = float(tip.target.size[1])/float(tip.origsize[1])
            
            if scale_x > scale_y:
                tip.scale = scale_y
            else:
                tip.scale = scale_x
            
            #we want our top-left corner to be in the middle of the thing we're attaching to...
            offset_x = 75 * tip.scale
            offset_y = (tip.origsize[0] - 40) * tip.scale
            
            global_offset_x = tip.offset[0]
            global_offset_y = tip.offset[1]
            
            #Does this object have a center_pos? If so, use that. If not, do it ourselves.
            if tip.target.center != None:
                tip.pos = tip.target.center[0] + (tip.origsize[0] * tip.scale * 0.25) + global_offset_x, tip.target.center[1] - (tip.origsize[1] * tip.scale * 0.10) + global_offset_y
            else:
                tip.pos = tip.target.pos[0] + tip.target.size[0]/2 - offset_x + global_offset_x, tip.target.pos[1] + tip.target.size[1]/2 - offset_y + global_offset_y
            
            tip.anim.pos = tip.pos
            tip.anim.scale = tip.scale
            tip.anim.opacity = tip.opacity
            tip.anim.rotation = tip.rotation
            
            tip.anim.on_draw()
            
            #Check on our delay timing.
            if not tip.shown:
                tip.delay = tip.delay - dt
                if tip.delay < 0:
                    tip.shown = True
                    tip.start_animations('show')
            
            #Check on our requirements
            if len(tip.requirements) < 1:
                deletetips.append(tip)
        
        for tip in deletetips:
            self.tips.remove(tip)
            self.remove_widget(tip)
        
        super(MTTouchTip, self).on_draw()
            
    
    def draw(self):
        for tip in self.tips:
            tip.anim.draw()
        super(MTTouchTip, self).draw()

        
MTWidgetFactory.register('MTTouchTip', MTTouchTip)