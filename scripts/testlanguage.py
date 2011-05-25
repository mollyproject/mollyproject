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
        if char == '%':
            in_formatter = 1
        if in_formatter > 0:
            r += char
            if in_formatter == 2:
                in_formatter = 0
            if char == ')':
                in_formatter = 2
        else:
            r += INVERSIONS.get(char, char)
    return r

if __name__ == '__main__':
    import sys
    
    msgs = []
    this_msg = ''
    in_msgid = False
    
    with open(sys.argv[1], encoding='utf-8') as fd:
        for line in fd:
            if line[:5] == 'msgid':
                in_msgid = True
                this_msg += line[7:-2] + '\n'
            elif line[:6] == 'msgstr':
                in_msgid = False
                msgs.append(this_msg)
                this_msg = ''
            elif in_msgid:
                this_msg += line[1:-2] + '\n'
    with open(sys.argv[1], 'w', encoding='utf-8') as fd:
        for msg in msgs:
            print >>fd, "msgid ",
            for line in msg.split('\n')[:-1]:
                print >> fd, "\"%s\"" % line
            print >>fd, "msgstr ",
            for line in invert(msg).split('\n')[:-1]:
                print >> fd, "\"%s\"" % line