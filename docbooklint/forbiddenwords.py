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
from docbooklint.linter import *
from docbooklint.xmlutils import *

class ForbiddenWord(DocBookError):
    def __init__(self, node, word):
        DocBookError.__init__(self, node)
        self.word = word

    def __str__(self):
        return 'Forbidden word: "%s" in context "%s..."'%(self.word, self.node.wholeText.strip()[:100])

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

if __name__=='__main__':
    unittest.main()
