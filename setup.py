from setuptools import setup

setup(
    name='CcMe',
    version='1.2',
    description='Trac plugin for handling a Cc button without TICKET_CHGPROP perms',
    author="The MacPorts Project",
    author_email="portmgr@macports.org",
    packages=['ccme'],
    entry_points = {
        'trac.plugins': [
            'ccme.ccme = ccme.ccme',
        ]
    },
    package_data = {
        'ccme': ['htdocs/css/*.css']
    }
)
