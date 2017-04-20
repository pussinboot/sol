# defines global variables
import os, pickle

##### ##### ####  #####
  #   #   # #   # #   #
  #   ##### ####  #####


class GlobalConfig:
	"""docstring for GlobalConfig"""
	def __init__(self,load_file=None):
		self.dict = self.__dict__
		self.default_options = {
		# sol params

		'DEBUG'					: True,
		'SAVEDATA_DIR'			: './savedata',
		'SCROT_DIR'				: './scrot',
		'NO_LAYERS'				: 2,
		'NO_Q'					: 8,
		'NO_LP'					: 8,
		'DEFAULT_SENSITIVITY'	: 0.005, # control hacks
		'IGNORED_DIRS'			: ['dxv','C:\\','C:/','VJ'],

		# model params
		'MODEL_SELECT'						: 'RESOLUME',
		'MODEL_SELECT_OPTIONS'				: ['RESOLUME', 'MEMEPV', 'ISADORA'],
		'RESOLUME_SAVE_DIR'					: '',
		'SUPPORTED_FILETYPES'				: ['.mov', '.webm', '.mp4','.avi'],
		'EXTERNAL_PLAYER_SELECT'			: 'MEMEPV',
		'EXTERNAL_PLAYER_SELECT_OPTIONS'	: ['MEMEPV','EXTERNAL_PLAYER'],
		# 'MEMEPV_SCRIPT_PATH'				: 'C:\\code\\vj\\memepv\\test.js',
		'MEMEPV_SCRIPT_PATH'				: 'C:\\Users\\leo\\Documents\\Code\\vj\\memepv\\test.js',
		'EXTERNAL_PLAYER_COMMAND'			: '',

		# gui params
		'ALWAYS_ON_TOP' 	: True,
		'THUMB_W' 			: 160,
		'REFRESH_INTERVAL'  : 166,
		'FFMPEG_PATH'		: '',
		'NO_FRAMES'			: 5,
		'THUMBNAIL_WIDTH'	: 192,
		}

		self.default_options['RESOLUME_SAVE_DIR'] = os.path.expanduser(os.sep.join(['~','Documents','Resolume Arena 5','compositions']))

		self.load(load_file)

	def save(self,save_file=None):
		pass

	def load(self,load_file=None):
		if load_file is None:
			for k,v in self.default_options.items():
				self.dict[k] = v





