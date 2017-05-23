from setuptools import setup, find_packages
import os

packages = find_packages()


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


config = {
    'name': 'sol_vj',
    'description': 'sol - fixes for resolume',
    'long_description': read('README_pip.md'),
    'author': 'pussinboots',
    'author_email': 'mkaynospam@gmail.com',
    'url': 'https://github.com/pussinboot/sol',
    'license': 'MIT',
    'version': '2.0.0',
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
