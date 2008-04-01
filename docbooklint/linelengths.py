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
from docbooklint.linter import *
from docbooklint.xmlutils import *

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


