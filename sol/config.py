# defines global variables
import os

##### ##### ####  #####
  #   #   # #   # #   #
  #   ##### ####  #####

# give this a gui and save these things to a pickle
DEBUG = True 

# actual magi params
NO_LAYERS = 2
NO_Q = 8 # cue points
NO_LP = 8

### gui
ALWAYS_ON_TOP = True

# thumbnail stuff..
THUMBNAIL_WIDTH = 192 # what size thumbnails to generate
THUMB_W = 160 # what size to display thumbnails at
REFRESH_INTERVAL = 166 # time in ms between frames
NO_FRAMES = 5

# model selection
MODEL_SELECT_OPTIONS = ['RESOLUME', 'MEMEPV', 'ISADORA']
MODEL_SELECT = 'RESOLUME'

# resomeme
RESOLUME_SAVE_DIR = "{0}{1}".format(os.environ['USERPROFILE'],"\\Documents\\Resolume Arena 5\\compositions")

# memepv
EXTERNAL_PLAYER_SELECT_OPTIONS = ['MEMEPV','EXTERNAL_PLAYER']
EXTERNAL_PLAYER_SELECT = 'MEMEPV'
# MEMEPV_SCRIPT_PATH = 'C:\\code\\vj\\memepv\\test.js'
MEMEPV_SCRIPT_PATH = 'C:\\Users\\leo\\Documents\\Code\\vj\\memepv\\test.js'
EXTERNAL_PLAYER_COMMAND = ''

# control hacks
DEFAULT_SENSITIVITY = 0.005 # how many seconds the default control adjustment is

# filetypes
SUPPORTED_FILETYPES = ('.mov', '.webm', '.mp4','.avi')

# ignored directory names
IGNORED_DIRS = ['dxv','C:\\','C:/','VJ']

SAVEDATA_DIR = './savedata'

# FFMPEG STUFF
FFMPEG_PATH = ''
# harcoded tk dimensions




# i think i have to return the frame as well so can hide/unhide dynamically whoops