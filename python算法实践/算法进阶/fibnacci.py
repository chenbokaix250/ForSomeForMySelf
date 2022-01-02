# -*- coding: utf-8 -*-
'''
@Time    : 2021/1/5 6:42 下午
@Author  : chenbokai
@File    : fibnacci.py
'''

def fibnacci(n):
    if n==1 or n ==2:
        return 1
    else:
        return fibnacci(n-1) + fibnacci(n-2)

print(fibnacci(4))