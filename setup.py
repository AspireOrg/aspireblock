#!/usr/bin/env python3

from setuptools import setup, find_packages, Command
from setuptools.command.install import install as _install
import os
import sys

from aspireblock.lib import config


class generate_configuration_files(Command):
    description = "Generate configfiles from old aspire-server and/or gaspd config files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from aspireblock.lib import config_util
        config_util.generate_config_files()


class install(_install):
    description = "Install aspireblock and dependencies"

    def run(self):
        caller = sys._getframe(2)
        caller_module = caller.f_globals.get('__name__', '')
        caller_name = caller.f_code.co_name
        if caller_module == 'distutils.dist' or caller_name == 'run_commands':
            _install.run(self)
        else:
            self.do_egg_install()
        self.run_command('generate_configuration_files')


required_packages = [
    'appdirs==1.4.0',
    'prettytable==0.7.2',
    'python-dateutil==2.5.3',
    'flask==0.11.1',
    'json-rpc==1.10.3',
    'pytest==2.9.2',
    'pycoin==0.77',
    'python-bitcoinlib==0.7.0',
    'pymongo==3.2.2',
    'gevent==1.1.1',
    'greenlet==0.4.9',
    'grequests==0.3.0',
    'redis==2.10.5',
    'pyzmq==15.2.0',
    'pillow==3.2.0',
    'lxml==3.6.0',
    'jsonschema==2.5.1',
    'strict_rfc3339==0.7',
    'rfc3987==1.3.6',
    'aniso8601==1.1.0',
    'pygeoip==0.3.2',
    'colorama==0.3.7',
    'configobj==5.0.6',
    'repoze.lru==0.6'
]

setup_options = {
    'name': 'aspireblock',
    'version': config.VERSION,
    'author': 'Aspire Developers',
    'author_email': 'admin@aspirecrypto.com',
    'maintainer': 'Aspire Developers',
    'maintainer_email': 'admin@aspirecrypto.com',
    'url': 'http://aspirecrypto.com',
    'license': 'MIT',
    'description': 'aspireblock server',
    'long_description': 'Implements support for extended functionality for aspire-lib',
    'keywords': 'aspire, gasp, aspireblock',
    'classifiers': [
        "Programming Language :: Python",
    ],
    'download_url': 'https://github.com/AspireOrg/aspireblock/releases/tag/%s' % config.VERSION,
    'provides': ['aspireblock'],
    'packages': find_packages(),
    'zip_safe': False,
    'setup_requires': ['appdirs', ],
    'install_requires': required_packages,
    'include_package_data': True,
    'entry_points': {
        'console_scripts': [
            'aspireblock = aspireblock:server_main',
        ]
    },
    'cmdclass': {
        'install': install,
        'generate_configuration_files': generate_configuration_files
    },
    'package_data': {
        'aspireblock.schemas': ['asset.schema.json', 'feed.schema.json'],
    }
}

if os.name == 'nt':
    sys.exit('Windows installs not supported')

setup(**setup_options)
