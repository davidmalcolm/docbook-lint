#!/usr/bin/env python
# Copyright (c) 2008 Red Hat, Inc. All rights reserved. This copyrighted material 
# is made available to anyone wishing to use, modify, copy, or 
# redistribute it subject to the terms and conditions of the GNU General 
# Public License v.2.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Author: David Malcolm

import unittest
import xml.dom.minidom
import xml.dom.ext
import sys

#
# Base class for tests
#
class DocBookTest:
    def perform_test(self, reporter, dom):
        raise NotImplementedError

#
# Base class for errors
#
class DocBookError:
    def __init__(self, node):
        self.node = node

    def get_context_str(self):
        maxLen = 50
        str = self.node.wholeText.strip()
        if len(str)>maxLen:
            shortStr = "%s..."%str[:maxLen]
        else:
            shortStr = str
        return 'in context "%s"'%shortStr

#
# Configuration
#

class Configuration:
    def __init__(self):
        self.maxLineLength = 80
        self.spellCheck = True
        self.defaultLangCode = "en_US"
        self.forbiddenWords = []

#
# Various ways of reporting errors:
#
class Reporter:
    """Policy for reporting errors/warnings: abstract base class"""
    def handle_warning(self, warning):
        raise NotImplementedError

class ExceptionReporter(Reporter):
    """Reportin policy: raise issues as exceptions"""
    def handle_warning(self, warning):
        raise warning

class PrintingReporter(Reporter):
    """
    Reporting policy: printing messages to a file object
    """
    def __init__(self, outputFileObj, inputFilename):
        self.outputFileObj = outputFileObj
        self.inputFilename = inputFilename
        self.numWarnings = 0

    def handle_warning(self, warning):
        print >> self.outputFileObj, "%s"%(str(warning))
        self.numWarnings += 1

class StdoutReporter(PrintingReporter):
    """
    A reporter which handles errors/warnings by printing messages to stdout
    """
    def __init__(self, inputFilename):
        PrintingReporter.__init__(self, sys.stdout, inputFilename)
    
class StderrReporter(PrintingReporter):
    """
    A reporter which handles errors/warnings by printing messages to stderr
    """
    def __init__(self, inputFilename):
        PrintingReporter.__init__(self, sys.stderr, inputFilename)

#
# The linter itself:
#
class DocBookLinter:
    def __init__(self, reporter, config):
        from docbooklint.fedoranamingconventions import DocBookFedoraIdNamingConvention
        from docbooklint.forbiddenwords import DocBookForbiddenWords
        from docbooklint.linelengths import DocBookLineLengths
        from docbooklint.spellcheck import DocBookSpellChecker

        self.reporter = reporter
        self.config = config

        # Gather the tests that we're going to perform:
        self.tests = []

        self.tests.append(DocBookLineLengths(self.config.maxLineLength))
        
        if self.config.spellCheck:
            self.tests.append(DocBookSpellChecker(self.config.defaultLangCode))

        self.tests.append(DocBookForbiddenWords(self.config.forbiddenWords))

        self.tests.append(DocBookFedoraIdNamingConvention())

    def test_file(self, filename):
        xmlDoc = xml.dom.minidom.parse(filename)
        self.test_dom(xmlDoc)

    def test_dom(self, dom):
        for test in self.tests:
            test.perform_test(self.reporter, dom)

def check_file(filename, config):
    "Check the file, outputting to stderr.  Return the number of warnings"
    reporter=StderrReporter(filename)
    linter = DocBookLinter(reporter, config=config)
    linter.test_file(filename)
    return reporter.numWarnings

#
# Unit tests
#

class SelfTest(unittest.TestCase):
    """Utility class for creating unit tests for the linter"""
    
    def make_xml(self, sourceStr):
        return xml.dom.minidom.parseString(sourceStr)

    def lint_string(self, sourceStr, config=None):
        if not config:
            config = Configuration()
        xmlDoc = self.make_xml(sourceStr)
        linter = DocBookLinter(reporter=ExceptionReporter(), config=config)
        linter.test_dom(xmlDoc)
