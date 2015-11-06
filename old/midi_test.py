import pygame.midi
pygame.midi.init()

import mido
#print(mido.get_input_names())
mido.set_backend('mido.backends.pygame')

#inport = mido.open_input()
print( mido.get_input_names())
inport = mido.open_input()