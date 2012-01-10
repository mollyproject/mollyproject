#!/usr/bin/env python
# coding: utf-8

from codecs import open

INVERSIONS = dict(zip(
    [ 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 
    'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
    'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    '1','2','3','4','5','6','7','8','9','0',
    '!','?','"',',','\'',')','(','_','^',
    
    '[',']','{','}','\\','/','<','>','.']
    ,
    
    [ u'ɐ', u'q', u'ɔ', u'p', u'ə', u'ɟ', u'ƃ', u'ɥ', u'ı', u'ɾ', u'ʞ', u'l', 
    u'ɯ', u'u', u'o', u'd', u'b', u'ɹ', u's', u'ʇ', u'n', u'ʌ', u'ʍ', u'x', u'ʎ', u'z',
    u'∀', u'q', u'Ɔ', u'p', u'Ǝ', u'Ⅎ', u'פ', u'H', u'I', u'ſ', u'丬', u'˥', u'W', u'N',
    u'O', u'Ԁ', u'Ό', u'ᴚ', u'S', u'⊥', u'∩', u'Λ', u'M', u'X', u'ʎ', u'Z',
    u'Ɩ', u'ᄅ', u'Ɛ', u'ㄣ', u'ϛ', u'9', u'Ɫ', u'8', u'6', u'0',
    u'¡', u'¿', u'„', u'\'', u',', u'(', u')', u'‾', u'v',
    
    u']', u'[', u'}', u'{', u'/', u'\\\\', u'>', u'<', u'˙']
))

def invert(chars):
    r = u''
    in_formatter = 0
    for char in chars:
        if char in ('%', '<'):
            in_formatter = 1
        if in_formatter > 0:
            r += char
            if in_formatter == 2:
                in_formatter = 0
            if char == ')':
                in_formatter = 2
            if char == '>':
                in_formatter = 0
        else:
            r += INVERSIONS.get(char, char)
    return r

def command(language_file):
    import sys
    
    msgs = []
    this_msg = ''
    this_plural = ''
    in_msgid = False
    
    with open(language_file, encoding='utf-8') as fd:
        for line in fd:
            if line[:12] == 'msgid_plural':
                in_msgid = 'p'
                this_plural += line[14:-2] + '\n'
            elif line[:5] == 'msgid':
                in_msgid = 's'
                this_msg += line[7:-2] + '\n'
            elif line[:6] == 'msgstr':
                in_msgid = False
                if this_msg or this_plural:
                    msgs.append((this_msg, this_plural))
                this_msg = ''
                this_plural = ''
            elif in_msgid:
                if in_msgid == 's':
                    this_msg += line[1:-2] + '\n'
                else:
                    this_plural += line[1:-2] + '\n'
    with open(language_file, 'w', encoding='utf-8') as fd:
        print >>fd, """
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2011-05-26 18:56+0100\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"""
        for msg, plural in msgs:
            if msg == '\n':
                continue
            print >>fd, "msgid ",
            for line in msg.split('\n')[:-1]:
                print >> fd, "\"%s\"" % line
            if plural:
                print >>fd, "msgid_plural ",
                for line in plural.split('\n')[:-1]:
                    print >> fd, "\"%s\"" % line
                print >>fd, "msgstr[0] ",
                for line in invert(msg).split('\n')[:-1]:
                    print >> fd, "\"%s\"" % line
                print >>fd, "msgstr[1] ",
                for line in invert(plural).split('\n')[:-1]:
                    print >> fd, "\"%s\"" % line
            else:
                print >>fd, "msgstr ",
                for line in invert(msg).split('\n')[:-1]:
                    print >> fd, "\"%s\"" % line
