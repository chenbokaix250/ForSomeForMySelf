# -*- coding: utf-8 -*-
'''
@Time    : 2021/1/5 4:34 下午
@Author  : chenbokai
@File    : change_money.py
'''


t = [100,50,20,5,1] # 面值
def change(t,n):
    m = [0 for _ in range(len(t))]
    for i,money in enumerate(t):
        m[i] = n //money
        n = n % money
    return m,n

print(change(t,376))



