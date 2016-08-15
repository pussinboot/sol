# defines global variables
import os


DEBUG = True 

# actual magi params
NO_LAYERS = 2
NO_Q = 8 # cue points
NO_LP = 8

### gui

# thumbnail stuff..
THUMBNAIL_WIDTH = 192 # what size thumbnails to generate
THUMB_W = 160 # what size to display thumbnails at
REFRESH_INTERVAL = 166 # time in ms between frames
NO_FRAMES = 5

# resomeme
RESOLUME_SAVE_DIR = "{0}{1}".format(os.environ['USERPROFILE'],"\\Documents\\Resolume Arena 5\\compositions")