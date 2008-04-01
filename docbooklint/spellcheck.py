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

import enchant
import re

class SpellcheckerError(DocBookError):
    def __init__(self, node, langCode, word):
        DocBookError.__init__(self, node)
        self.langCode = langCode
        self.word = word

    def __str__(self):
        return 'Possibly mispelled word for "%s": "%s" %s'%(self.langCode, self.word, self.get_context_str())

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
            if re.match(r"^[\d.]*$", word):
                return
            
            # Check the word:
            if not self.enchantDict.check(word):
                self.misspellings.append(SpellcheckerError(node, self.langCode, word))



        
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

numericSpellingExample="""<?xml version="1.0"?>
<article>
<para>
The quick brown fox jumps over 3.2 lazy dogs
</para>
</article>
"""

class TestSpellcheck(SelfTest):
    def test_spelling_mistake(self):
        "Ensure that spelling mistakes are flagged"
        self.assertRaises(SpellcheckerError, self.lint_string, misspellingExample)

    def test_dont_spellcheck_computeroutput(self):
        "Ensure that <computeroutput> doesn't get spellchecked"
        self.lint_string(dontSpellcheckExample)

    def test_dont_spellcheck_numbers(self):
        "Ensure that numbers don't get spellchecked"
        self.lint_string(numericSpellingExample)

