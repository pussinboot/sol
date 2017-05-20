# package and distribution management
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os

from pip.req import parse_requirements
install_reqs = parse_requirements('./requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

config = {
    'name': 'sol',
    'description': 'sol - fixes for resolume',
    'long_description': read('README.md'),
    'author': 'pussinboots',
    'url': 'https://github.com/pussinboot/sol',
    'license':'MIT',
    'version': '2.0.0',
    'install_requires': reqs,
    'packages': ['sol'],
    'package_data' :{
        'empty_clip': ['sol/gui/tk_gui/sample_clip.png'],
        'empty_loop_thumb': ['sol/gui/tk_gui/sample_thumb.png'],
    },
    'classifiers' :[
        "Development Status :: 5 - Beta",
        'Intended Audience :: Developers',
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        'Programming Language :: Python :: 3',
    ],
    'keywords' : 'vj, resolume, video',
    'entry_points' :{
        'console_scripts': [
            # 'sol = sol.test_gui:main',
            # 'sol_mt = sol.mt_gui',
            'sol_cl = sol.magi'
        ],
    },
}

setup(**config)