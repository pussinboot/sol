class MemePV:
    """
    defines the memepv api
    """

    def __init__(self, no_layers):

        self.no_layers = 2
        # for updating current clip positions
        self.current_clip_pos = [None] * no_layers
        # index current_clip_pos by layer
        self.clip_pos_addr = [None] * no_layers

        for n in range(no_layers):
            self.clip_pos_addr[n] = "/{}/time".format(n)
        self.external_looping = True
        self.lt_lu = {'d': 0, 'b': 1}

    def play(self, layer):
        return ('/{}/play'.format(layer), 1)

    def pause(self, layer):
        return ('/{}/pause'.format(layer), 1)

    def reverse(self, layer):
        return ('/{}/reverse'.format(layer), 1)

    def random(self, layer):
        return ('/{}/random'.format(layer), 1)

    def set_clip_pos(self, layer, pos):
        return ('/{}/seek'.format(layer), pos)

    def select_clip(self, layer, clip):
        return ('/{}/load'.format(layer), clip.f_name)

    def clear_clip(self, layer):
        return ('/{}/clear'.format(layer), 1)

    def set_playback_speed(self, layer, speed):
        return ('/{}/speed'.format(layer), speed)

    # looping

    def set_loop_a(self, layer, clip, a=0, b=1):
        if a is None:
            a = 0
        return ('/{}/loop_a'.format(layer), a)

    def set_loop_b(self, layer, clip, a=0, b=1):
        if b is None:
            b = 1
        return ('/{}/loop_b'.format(layer), b)

    def set_loop_type(self, layer, lt):
        if lt in self.lt_lu:
            lt = self.lt_lu[lt]
        else:
            lt = 0
        return ('/{}/loop_type'.format(layer), lt)
