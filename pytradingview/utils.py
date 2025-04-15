import math, random

def genSessionID(type='xs'):
    id = ''
    c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    for i in range(12):
        id += c[math.floor(random.random()*len(c))]
    return  f'{type}_{id}'
