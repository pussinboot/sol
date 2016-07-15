# package and distribution management
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from pip.req import parse_requirements
install_reqs = parse_requirements('./requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]


config = {
    'name': 'sol',
    'description': 'sol vj soft',
    'author': 'pussinboots',
    'url': 'https://github.com/pussinboot/sol',
    'license':'MIT',
    'version': '2.0',
    'install_requires': reqs,
    'packages': ['sol'],
    'scripts': []
}

setup(**config)