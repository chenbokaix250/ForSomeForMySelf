# -*- coding: utf-8 -*-
'''
@Time    : 2021/1/12 10:31 上午
@Author  : chenbokai
@File    : gcd.py
'''

def gcd(a,b):
    if b == 0:
        return a
    else:
        return gcd(b,a%b)

def gcd2(a,b):
    while b > 0:
        r = a % b
        a = b
        b = r
    return a
print(gcd(12,16))