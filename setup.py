from setuptools import setup, find_packages

packages = find_packages()

READMEME = """sol is an interactive database of clips

it lets you organize and search for clips plus keep associated parameters, cue points, loop points, thumbnails and tags

it controls playback and adds some missing features to re[sol]ume

MIT licensed

# setup instructions

you will need `ffmpeg` and its associated `ffprobe`

`pip install sol_vj`"""

config = {
    'name': 'sol_vj',
    'description': 'sol - fixes for resolume',
    'long_description': READMEME,
    'author': 'pussinboots',
    'author_email': 'mkaynospam@gmail.com',
    'url': 'https://github.com/pussinboot/sol',
    'license': 'MIT',
    'version': '2.1.0',
    'install_requires': [
        'python-osc>=1.6',
        'lxml>=3.6.0',
        'Pillow>=4.1.0'
    ],
    'packages': packages,
    'package_data': {
        'sol.gui.tk_gui': ['sample_clip.png', 'sample_thumb.png'],
    },
    'classifiers': [
        "Development Status :: 4 - Beta",
        'Intended Audience :: Developers',
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        'Programming Language :: Python :: 3',
    ],
    'keywords': 'vj, resolume, video',
    'entry_points': {
        'console_scripts': [
            'sol = sol.test_gui:main',
            'sol_mt = sol.mt_gui:main',
            'sol_cl = sol.magi:main'
        ],
    },
}

setup(**config)
