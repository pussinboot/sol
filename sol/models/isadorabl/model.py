class IsadoraBL:
    """
    defines the isadorabl api
    """
    def __init__(self,no_layers):
        self.no_layers = 2 #no_layers

        # for updating current clip positions
        self.current_clip_pos = [None] * no_layers
        # index current_clip_pos by layer
        self.clip_pos_addr = [None] * no_layers
        # keep track of last speed
        self.current_clip_spd = [1] * no_layers

        for n in range(no_layers):
            self.clip_pos_addr[n] = "/layer{}/position".format(n+1)

        self.external_looping = True
        self.lt_lu = {'d':1,'b':2} # loop type lookup


    def play(self,layer):
        last_spd = self.current_clip_spd[layer]
        if last_spd < 0:
            last_spd *= -1
        return self.set_playback_speed(layer,last_spd)

    def pause(self,layer):
        last_spd = self.current_clip_spd[layer]
        tor = self.set_playback_speed(layer,0)      
        self.current_clip_spd[layer] = last_spd
        return tor

    def reverse(self,layer):
        last_spd = self.current_clip_spd[layer]
        if last_spd > 0:
            last_spd *= -1
        return self.set_playback_speed(layer,last_spd)

    # not implemented yet
    # have to import random
    # then call random.random()
    def random(self,layer):
        return ('/random',1)

    def set_clip_pos(self,layer,pos):
        addr = "/layer{}/seek".format(layer+1)
        return (addr, pos*100)

    def select_clip(self,layer,clip):
        addr = "/layer{}/clip".format(layer+1)
        return (addr, int(clip.command))

    def clear_clip(self,layer):
        addr = "/layer{}/clip".format(layer+1)
        return (addr, 0)

    def set_playback_speed(self,layer,speed):
        self.current_clip_spd[layer] = speed
        addr = "/layer{}/speed".format(layer+1)
        return (addr, speed) 

    ### looping
    def set_loop_type(self,layer,lt):
        addr = "/layer{}/loop".format(layer+1)
        loop_type = self.lt_lu[lt]
        return (addr, loop_type)

    def set_loop_a(self,layer,clip,a=None,b=None):
        if a is None: a = 0
        addr = "/layer{}/loop/a".format(layer+1)
        a = 100 * a
        return (addr, a)

    def set_loop_b(self,layer,clip,a=None,b=None):
        if a is None: a = 0
        if b is None: b = 1
        addr = "/layer{}/loop/b".format(layer+1)
        b = 100 * (b-a) # actually duration
        return (addr, b)
