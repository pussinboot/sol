# defines global variables
import os
import pickle

import sol.themer as themer

class SingletonDecorator:
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.klass(*args, **kwds)
        return self.instance


@SingletonDecorator
class GlobalConfig:
    def __init__(self, load_defaults=False):
        self.dict = self.__dict__

        self.root_path = os.path.expanduser("~/.sol")
        if not os.path.exists(self.root_path):
            os.mkdir(self.root_path)

        self.default_options = {
            # sol params
            'DEBUG'					: True,
            'SAVEDATA_DIR'			: './savedata',
            'SCROT_DIR'				: './scrot',
            'NO_LAYERS'				: 2,
            'NO_Q'					: 8,
            'NO_LP'					: 8,
            'DEFAULT_SENSITIVITY'	: 0.005,  # control hacks
            'IGNORED_DIRS'			: ['C:\\', 'dxv', 'VJ'],

            # network params
            'OSC_PORT'			: 7001,
            'MTGUI_ENABLED'		: False,
            'MTGUI_IP_ADDR'		: '127.0.0.1',

            # model params
            'MODEL_SELECT'						: 'RESOLUME',
            'MODEL_SELECT_OPTIONS'				: ['RESOLUME', 'MPV', 'ISADORA'],
            'RESOLUME_SAVE_DIR'					: '',
            'SUPPORTED_FILETYPES'				: ['.mov', '.webm', '.mp4', '.avi'],
            'XTERNAL_PLAYER_SELECT'				: 'EXTERNAL_PLAYER',
            'EXTERNAL_PLAYER_SELECT_OPTIONS'	: ['MEMEPV', 'EXTERNAL_PLAYER'],
            'MEMEPV_SCRIPT_PATH'				: 'C:\\code\\vj\\memepv\\test.js',
            'EXTERNAL_PLAYER_COMMAND'			: '',

            # gui params
            'ALWAYS_ON_TOP' 	: True,
            'THUMB_W' 			: 160,
            'REFRESH_INTERVAL'  : 200,
            'FFMPEG_PATH'		: '',
            'NO_FRAMES'			: 5,
            'THUMBNAIL_WIDTH'	: 192,
            'FONT_WIDTHS'		: {},
            'FONT_HEIGHT'		: 10,
            'FONT_AVG_WIDTH'	: 5,
            'SELECTED_THEME'    : 'light_gray',
        }

        self.default_options['RESOLUME_SAVE_DIR'] = os.path.expanduser(
            os.sep.join(['~', 'Documents', 'Resolume Arena 5', 'compositions']))
        self.default_options['SAVEDATA_DIR'] = os.path.join(
            self.root_path, 'savedata')
        self.default_options['SCROT_DIR'] = os.path.join(
            self.root_path, 'scrot')

        self.config_savefile = os.path.join(
            self.default_options['SAVEDATA_DIR'], 'config.pickle')

        if load_defaults:
            self.load()
        else:
            self.load(self.config_savefile)

        check_folders = ['SAVEDATA_DIR', 'SCROT_DIR']
        for cf in check_folders:
            folder = self.__dict__[cf]
            if not os.path.exists(folder):
                os.mkdir(folder)

        # setup theme
        self.themer = themer
        self.CURRENT_THEME = themer.config_setup(self)

    def save(self):
        try:
            with open(self.config_savefile, 'wb') as save_handle:
                pickle.dump(self.dict, save_handle,
                            protocol=pickle.HIGHEST_PROTOCOL)
            if self.DEBUG:
                print('saved', self.config_savefile)
        except Exception as e:
            print(e)
            if self.DEBUG:
                print('failed to make config savedata')

    def load(self, load_file=None):
        defaults = self.default_options.items()
        if load_file is not None and os.path.exists(load_file):
            try:
                with open(load_file, 'rb') as save_handle:
                    load_dict = pickle.load(save_handle)
                self.__dict__ = load_dict
            except:
                if self.DEBUG:
                    print('failed to load config savedata\nloading defaults...')

        for k, v in defaults:
            if k not in self.dict:
                self.dict[k] = v
