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
import os.path

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


class XmlDoc:
    # Wrapper for a DOM
    def __init__(self, dom):
        self.dom = dom

    @classmethod
    def from_source(cls, sourceStr):
        return XmlDoc(xml.dom.minidom.parseString(sourceStr))

class XmlFile(XmlDoc):
    # Wrapper for a DOM loaded from a file
    def __init__(self, filename):
        self.filename = filename
        self.basePath = os.path.dirname(filename)
        self.dom = xml.dom.minidom.parse(filename)

        
class XmlVisitor:
    """
    Base class for a visiting nodes of an XML DOM tree
    """
    def visit_file(self, filename):
        xmlDoc = XmlFile(filename)
        self.recurse_nodes(xml.dom, xmlDoc)

    def visit_doc(self, xmlDoc):
        self.recurse_nodes(xmlDoc.dom, xmlDoc)

    def recurse_nodes(self, node, xmlDoc):
        "Depth-first traversal of tree"
        self.visit(node)

        child = node.firstChild
        while child:
            self.recurse_nodes(child, xmlDoc)
            child = child.nextSibling

        # recurse into other files via XInclude:
        if is_named_element(node, 'include', 'http://www.w3.org/2001/XInclude'):
            filename = node.getAttribute('href')
            if not os.path.isabs(filename):
                filename = os.path.join(xmlDoc.basePath, filename)
            includedXmlDoc = XmlFile(filename)
            self.recurse_nodes(includedXmlDoc.dom, includedXmlDoc)

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

