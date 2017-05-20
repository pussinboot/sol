from setuptools import setup, find_packages
import os

from pip.req import parse_requirements
install_reqs = parse_requirements('./requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]
packages = find_packages()


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


config = {
    'name': 'sol',
    'description': 'sol - fixes for resolume',
    'long_description': read('README.md'),
    'author': 'pussinboots',
    'url': 'https://github.com/pussinboot/sol',
    'license': 'MIT',
    'version': '2.0.0',
    'install_requires': reqs,
    'packages': packages,
    'package_data': {
        'sol.gui.tk_gui': ['sample_clip.png', 'sample_thumb.png'],
    },
    'classifiers': [
        "Development Status :: 5 - Beta",
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
