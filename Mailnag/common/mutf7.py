#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
This awesome piece of code is intented to encode and decode modified UTF-7 
(the one that is used for IMAP folder names)

encode_mutf7(text) - to encode
decode_mutf7(text) - to decode
'''

__author__ = "https://github.com/cheshire-mouse"
__license__ = "WTFPL v. 2"

import base64
import re

ascii_codes = set(range(0x20,0x7f))

def __get_ascii(text):
    pos = 0
    for c in text:
        code=ord(c)
        if ord(c) not in ascii_codes :
            break
        pos += 1
    return text[:pos].encode('ascii')

def __remove_ascii(text):
    pos = 0
    for c in text:
        if ord(c) not in ascii_codes :
            break
        pos += 1
    return text[pos:]

def __get_nonascii(text):
    pos = 0
    for c in text:
        code=ord(c)
        if ord(c) in ascii_codes :
            break
        pos += 1
    return text[:pos]

def __remove_nonascii(text):
    pos = 0
    for c in text:
        if ord(c) in ascii_codes :
            break
        pos += 1
    return text[pos:]

def __encode_modified_utf7(text):
    #modified base64 - good old base64 without padding characters (=)
    result = base64.b64encode(text.encode('utf-16be')).rstrip('=')
    result = result.replace('/',',')
    result = '&' + result + '-'
    return result

def encode_mutf7(text):
    result = ""
    text = text.replace('&','&-')
    while len(text) > 0:
        result += __get_ascii(text)
        text = __remove_ascii(text)
        if len(text) > 0:
            result += __encode_modified_utf7(__get_nonascii(text))
            text = __remove_nonascii(text)
    return result

def __decode_modified_utf7(text):
    if text == '&-':
        return '&'
    #remove leading & and trailing -
    text_mb64 = text[1:-1]
    text_b64 = text_mb64.replace(',','/')
    #back to normal base64 with padding
    while len(text_b64) % 4 != 0:
        text_b64 += '='
    text_u16 = base64.b64decode(text_b64)
    result = text_u16.decode('utf-16be')
    return result

def decode_mutf7(text):
    rxp = re.compile('&[^&-]*-')
    match = rxp.search(text)
    while ( match ):
        encoded_text = match.group(0)
        decoded_text = __decode_modified_utf7(encoded_text)
        text = rxp.sub(decoded_text,text, count=1)
        match = rxp.search(text)
    result = text
    return result

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

