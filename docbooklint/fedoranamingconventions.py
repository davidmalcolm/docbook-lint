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

class IdDoesNotStartWithPrefix(DocBookError):
    def __init__(self, node, id, expectedPrefix):
        DocBookError.__init__(self, node)
        self.id = id
        self.expectedPrefix = expectedPrefix

    def __str__(self):
        return 'Node <%s>\'s id ("%s") does not start with prefix "%s"'%(self.node.nodeName, self.id, self.expectedPrefix)

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
