# -*- coding: utf-8 -*-
'''
@Time    : 2021/1/5 5:57 下午
@Author  : chenbokai
@File    : number_join.py
'''

from functools import cmp_to_key
li = [32,94,128,1286,6,71]

def xy_cmp(x,y):
    if x+y < y+x:
        return 1
    elif x+y > y+x:
        return -1
    else:
        return 0


def number_join(li):
    li = list(map(str,li))
    li.sort(key=cmp_to_key(xy_cmp))
    return "".join(li)

print(number_join(li))