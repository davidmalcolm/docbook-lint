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

import xml.dom.minidom
import xml.dom.ext

#
# XML utilities:
#

def is_textual(node):
    return node.nodeType in [xml.dom.minidom.Node.TEXT_NODE, xml.dom.minidom.Node.CDATA_SECTION_NODE]

def is_element(node):
    return node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE

def is_named_element(node, elementName, nsURI=None):
    if is_element(node):
        if node.localName == elementName:
            if node.namespaceURI == nsURI:
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

