#!/usr/bin/env python
__author__ = "David Malcolm <dmalcolm@redhat.com>"

from distutils.core import setup
from distutils.command.bdist_rpm import bdist_rpm

setup (
        name = 'docbooklint',
        version = '0.0.1',
        description = """Tool for detecting problems in DocBook XML sources.""",
        author = """David Malcolm <dmalcolm@redhat.com>""",
        author_email = 'dmalcolm@redhat.com',
        packages = ['docbooklint'],
        cmdclass = {
                'bdist_rpm': bdist_rpm
                },
        scripts=['docbooklint/docbook-lint']
)
