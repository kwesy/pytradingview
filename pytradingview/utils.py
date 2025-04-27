import math
import random
import re

def genSessionID(type='xs'):
    id = ''
    c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    for i in range(12):
        id += c[math.floor(random.random()*len(c))]
    return  f'{type}_{id}'

def strip_html_tags(text):
    return re.sub(r"<[^>]+>", "", text)