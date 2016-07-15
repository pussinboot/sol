# package and distribution management
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from pip.req import parse_requirements
install_reqs = parse_requirements('./requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]


config = {
    'description': 'sol vj soft',
    'author': 'pussinboots',
    'url': 'https://github.com/pussinboot/sol',
    'download_url': 'https://github.com/pussinboot/sol.git',
    'author_email': 'leooooo@bu.edu',
    'version': '2.0',
    'install_requires': reqs,
    'packages': ['sol'],
    'scripts': [],
    'name': 'sol'
}

setup(**config)