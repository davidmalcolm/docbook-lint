#!/usr/bin/env python
# Copyright (c) 2006 Red Hat, Inc. All rights reserved. This copyrighted material 
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
"""
Classes for detecting certain errors in DocBook files.

Note that I'm not currently bothering with DTD validation - there are plenty of
other tools to achieve this.
"""
import xml.dom.minidom
import xml.dom.ext
import unittest
import sys
import enchant
import re
#
# XML utilities:
#

def is_textual(node):
    return node.nodeType in [xml.dom.minidom.Node.TEXT_NODE, xml.dom.minidom.Node.CDATA_SECTION_NODE]

def is_element(node):
    return node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE

def is_named_element(node, elementName):
    if is_element(node):
        if node.nodeName==elementName:
            # Doesn't support namespaces; not needed for DocBook
            return True
    return False

class XmlVisitor:
    """
    Base class for a visiting nodes of an XML DOM tree
    """
    def visit_file(self, filename):
        xmlDoc = xml.dom.minidom.parse(filename)
        self.recurse_nodes(xmlDoc)

    def visit_dom(self, dom):
        self.recurse_nodes(dom)

    def recurse_nodes(self, node):
        "Depth-first traversal of tree"
        self.visit(node)

        child = node.firstChild
        while child:
            self.recurse_nodes(child)
            child = child.nextSibling

    def visit(self, node):
        #print node
        #print dir(node)
        if is_element(node):
            self.visit_element(node)

        if is_textual(node):
            self.visit_textual(node)

    def visit_element(self, node):
        raise NotImplementedError

    def visit_textual(self, node):
        raise NotImplementedError

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
# Various errors to report:
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

class InlineTextTooLong(DocBookError):
    def __init__(self, node):
        DocBookError.__init__(self, node)

    def __str__(self):
        wholeText = self.node.wholeText
        return 'Inline text too long: "%s" (%i characters)'%(wholeText, len(wholeText))

class LineTooLong(DocBookError):
    def __init__(self, node, line):
        DocBookError.__init__(self, node)
        self.line = line

    def __str__(self):
        return 'Line too long: "%s" (%i characters)'%(self.line, len(self.line))

class SpellcheckerError(DocBookError):
    def __init__(self, node, langCode, word):
        DocBookError.__init__(self, node)
        self.langCode = langCode
        self.word = word

    def __str__(self):
        return 'Possibly mispelled word for "%s": "%s" %s'%(self.langCode, self.word, self.get_context_str())

class ForbiddenWord(DocBookError):
    def __init__(self, node, word):
        DocBookError.__init__(self, node)
        self.word = word

    def __str__(self):
        return 'Forbidden word: "%s" in context "%s..."'%(self.word, self.node.wholeText.strip()[:100])

class IdDoesNotStartWithPrefix(DocBookError):
    def __init__(self, node, id, expectedPrefix):
        DocBookError.__init__(self, node)
        self.id = id
        self.expectedPrefix = expectedPrefix

    def __str__(self):
        return 'Node <%s>\'s id ("%s") does not start with prefix "%s"'%(self.node.nodeName, self.id, self.expectedPrefix)

#
# Multiple-language support:
#
#
# Various classes representing independent tests:
#
class DocBookTest:
    def perform_test(self, reporter, dom):
        raise NotImplementedError

class DocBookLineLengths(DocBookTest):
    def __init__(self, maxLineLength):
        self.maxLineLength = maxLineLength
        
    def perform_test(self, reporter, dom):
        visitor = DocBookLineLengths.Visitor(reporter, self.maxLineLength)
        visitor.visit_dom(dom)

    class Visitor(XmlVisitor):
        def __init__(self, reporter, maxLineLength):
            self.reporter = reporter
            self.maxLineLength = maxLineLength

        def visit_textual(self, node):
            pass

        def visit_element(self, node):
            #print node.nodeName
            if node.nodeName=='screen':
                # Crude check for length of lines:
                if node.firstChild:
                    if is_textual(node.firstChild):
                        wholeText = node.firstChild.wholeText
                        
                        lines = wholeText.splitlines()
                        for line in lines:
                            if len(line)>self.maxLineLength:
                                self.reporter.handle_warning(LineTooLong(node, line))
            elif node.nodeName=='computeroutput':
                # <computeroutput> is a non-verbatim inline environment, typically monospaced
                # Many toolchains appear to have the implicit assumption that only short
                # amounts of text will appear, and don't support line-breaking within it,
                # so it's thus useful to flag problems if a text node below it has a large number of characters
                if node.firstChild:
                    if is_textual(node.firstChild):
                        wholeText = node.firstChild.wholeText
                        if len(wholeText)>self.maxLineLength:
                            self.reporter.handle_warning(InlineTextTooLong(node.firstChild))
       

class DocBookSpellChecker(DocBookTest):
    def __init__(self, defaultLangCode):
        self.defaultLangCode = defaultLangCode

    def perform_test(self, reporter, dom):
        visitor = DocBookSpellChecker.Visitor(self.defaultLangCode)
        visitor.visit_dom(dom)        

        for lang in visitor.languages.itervalues():
                for misspelling in lang.misspellings:
                    reporter.handle_warning(misspelling)                  

    class Visitor(XmlVisitor):
        """Visitor that gathers spellchecking errors within the document"""
        def __init__(self, defaultLangCode):
            self.defaultLangCode = defaultLangCode
            self.languages = {}

        def __lazy_get_language(self, langCode):
            if not self.languages.has_key(langCode):
                self.languages[langCode]=DocBookSpellChecker.Language(langCode)
            return self.languages[langCode]

        def __should_spellcheck(self, textNode):
            # Don't spellcheck inside certain nodes:
            if is_named_element(textNode.parentNode, "computeroutput"):
                return False
            
            if is_named_element(textNode.parentNode, "filename"):
                return False
            
            if is_named_element(textNode.parentNode, "ulink"):
                return False
            
            if is_named_element(textNode.parentNode, "command"):
                return False
            
            if is_named_element(textNode.parentNode, "keycap"):
                return False

            if is_named_element(textNode.parentNode, "tag"):
                return False

            if is_named_element(textNode.parentNode, "screen"):
                return False

            return True

        def visit_textual(self, node):
            if self.__should_spellcheck(node):
                langCode = self.defaultLangCode #FIXME
                lang = self.__lazy_get_language(langCode)
        
                lines = node.wholeText.splitlines()
                for line in lines:
                    for word in line.strip().split(' '):
                        lang.check_word(node, word.strip(' .,()-:;<>'))

        def visit_element(self, node):
            pass
        
    class Language:
        """All spellcheck information relating to a particular language in the document"""
        def __init__(self, langCode):
            self.langCode = langCode
            self.enchantDict = enchant.Dict(langCode)
            self.misspellings = []

        def check_word(self, node, word):
            # print 'word: "%s"'%word
            
            # Don't spellcheck numbers:
            if re.match(r"^[\d]*$", word):
                return
            
            # Check the word:
            if not self.enchantDict.check(word):
                self.misspellings.append(SpellcheckerError(node, self.langCode, word))


class DocBookForbiddenWords(DocBookTest):
    def __init__(self, forbiddenWords):
        self.forbiddenWords = forbiddenWords
        
    def perform_test(self, reporter, dom):
        visitor = DocBookForbiddenWords.Visitor(self.forbiddenWords, reporter)
        visitor.visit_dom(dom)

    class Visitor(XmlVisitor):
        def __init__(self, forbiddenWords, reporter):
            self.forbiddenWords = forbiddenWords
            self.reporter = reporter

        def visit_textual(self, node):
            lines = node.wholeText.splitlines()
            for line in lines:
                for word in line.strip().split(' '):
                    word = word.strip(' .,()-:;')
                    if word in self.forbiddenWords:
                        self.reporter.handle_warning(ForbiddenWord(node, word))

        def visit_element(self, node):
            pass

class DocBookFedoraIdNamingConvention(DocBookTest):
    def perform_test(self, reporter, dom):
        visitor = DocBookFedoraIdNamingConvention.Visitor(reporter)
        visitor.visit_dom(dom)

    class Visitor(XmlVisitor):
        def __init__(self, reporter):
            self.reporter = reporter

        def visit_textual(self, node):
            pass

        def visit_element(self, node):
            if node.nodeName=='chapter':
                self.currentChapter = node

            if node.hasAttribute('id'):
                id = node.getAttribute('id')
                # print 'id="%s"'%id

                # Ensure id starts with correct prefix:
                prefixMap = {'preface':  'pr-',
                             'chapter':  'ch-',
                             'section':  'sn-',
                             'sect1':    's1-',
                             'sect2':    's2-',
                             'sect3':    's3-',
                             'sect4':    's4-',
                             'figure':   'fig-',
                             'table':    'tb-',
                             'appendix': 'ap-',
                             'part':     'pt-',
                             'example':  'ex-'}
                if prefixMap.has_key(node.nodeName):
                    expectedPrefix = prefixMap[node.nodeName]
                    if not id.startswith(expectedPrefix):
                        self.reporter.handle_warning(IdDoesNotStartWithPrefix(node, id, expectedPrefix))

                # FIXME: Ensure that section IDs contain the chapter ID suffix

                # FIXME: Ensure id is not too long:
            
            # FIXME: should we complain if one of these is missing an ID?


class Configuration:
    def __init__(self):
        self.maxLineLength = 80
        self.spellCheck = True
        self.defaultLangCode = "en_US"
        self.forbiddenWords = []

#
# The linter itself:
#
class DocBookLinter:
    def __init__(self, reporter, config):
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

def test_file(filename, config):
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
        
screenTagWithReasonableLineLengths="""<?xml version="1.0"?>
<article>
<title>Example of a <tag>screen</tag> with reasonable line lengths</title>
<screen>
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
</screen>
</article>
"""

screenTagWithUnreasonableLineLengths="""<?xml version="1.0"?>
<article>
<title>Example of a <tag>screen</tag> with unreasonable line lengths</title>
<screen>
The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog
</screen>
</article>
"""

okComputerTag="""<?xml version="1.0"?>
<article>
<title>Example of a reasonable <tag>computeroutput</tag></title>
<para>The output from <command>foo</command> is <computeroutput>The quick brown fox jumps over the lazy dog</computeroutput></para>
</article>
"""

computerTagWithTooMuchText="""<?xml version="1.0"?>
<article>
<title>Example of a <tag>computeroutput</tag> of unreasonable length</title>
<computeroutput>
The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog The quick brown fox jumps over the lazy dog
</computeroutput>
</article>
"""

class TestLineLengths(SelfTest):
    def test_screen_tag_with_reasonable_line_lengths(self):
        "Ensure no warnings for a reasonable screen tag"
        self.lint_string(screenTagWithReasonableLineLengths)

    def test_screen_tag_with_unreasonable_line_lengths(self):
        "Ensure a line that's too long is flagged as a warning"
        self.assertRaises(LineTooLong, self.lint_string, screenTagWithUnreasonableLineLengths)

    def test_ok_computeroutput(self):
        "Ensure that a long text node with line-breaks isn't flagged as a warning"
        self.lint_string(okComputerTag)

    def test_computeroutput_too_long(self):
        "Ensure a computeroutput that's too long is flagged as a warning"
        self.assertRaises(InlineTextTooLong, self.lint_string, computerTagWithTooMuchText)


misspellingExample="""<?xml version="1.0"?>
<article>
<para>
The quzck brown fox jumps over the lazy dog
</para>
</article>
"""

dontSpellcheckExample="""<?xml version="1.0"?>
<article>
<screen>
           CPU0              
  1:     465970        Phys-irq  i8042
  7:          0        Phys-irq  parport0
  8:          1        Phys-irq  rtc
  9:          0        Phys-irq  acpi
 12:    9284238        Phys-irq  i8042
 14:    3010970        Phys-irq  ide0
 15:         78        Phys-irq  ide1
 16:   13987066        Phys-irq  uhci_hcd:usb3, libata, peth0
 17:          0        Phys-irq  uhci_hcd:usb1, uhci_hcd:usb4
 18:          0        Phys-irq  uhci_hcd:usb2
 19:          0        Phys-irq  ehci_hcd:usb5
 20:      84700        Phys-irq  Intel ICH5
256:   93722638     Dynamic-irq  timer0
257:          0     Dynamic-irq  resched0
258:          0     Dynamic-irq  callfunc0
259:         85     Dynamic-irq  xenbus
260:          0     Dynamic-irq  console
NMI:          0 
LOC:          0 
ERR:          0
MIS:          0
</screen>
</article>
"""

class TestSpellcheck(SelfTest):
    def test_spelling_mistake(self):
        "Ensure that spelling mistakes are flagged"
        self.assertRaises(SpellcheckerError, self.lint_string, misspellingExample)

    def test_dont_spellcheck_computeroutput(self):
        "Ensure that <computeroutput> doesn't get spellchecked"
        self.lint_string(dontSpellcheckExample)

badWordsExample="""<?xml version="1.0"?>
<article>
<title>Excerpt<!-- from Book 1, Chapter 22 of Little Dorrit, by Charles Dickens --></title>
<para>Still, her youthful and ethereal appearance, her timid manner, the charm
of her sensitive voice and eyes, the very many respects in which she had
interested him out of her own individuality, and the strong difference between
herself and those about her, were not in unison, and were determined not to
be in unison, with this newly presented idea.</para>
</article>
"""

class TestForbiddenWords(SelfTest):
    def test_bad_word(self):
        "Ensure that forbidden words are flagged"
        config = Configuration()
        config.forbiddenWords = ['ethereal']
        self.assertRaises(ForbiddenWord, self.lint_string, badWordsExample, config)

badSectionId="""<?xml version="1.0"?>
<article>
<title>Example of a id value that doesn't match the Fedora documentation naming conventions</title>
<section id="example"><para>This is an example of a bad ID.</para>
</section>
</article>
"""

goodSectionId="""<?xml version="1.0"?>
<article>
<title>Example of a id value that matches the Fedora documentation naming conventions</title>
<section id="sn-example"><para>This is an example of a good ID.</para>
</section>
</article>
"""

class TestFedoraIdNamingConvention(SelfTest):
    def test_bad_section_id(self):
        self.assertRaises(IdDoesNotStartWithPrefix, self.lint_string, badSectionId)

    def test_good_section_id(self):
        self.lint_string(goodSectionId)

if __name__=='__main__':
    unittest.main()
