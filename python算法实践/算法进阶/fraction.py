# -*- coding: utf-8 -*-
'''
@Time    : 2021/1/12 10:33 上午
@Author  : chenbokai
@File    : fraction.py
'''


class Fraction:
    def __init__(self,a,b):
        self.a = a
        self.b = b
        x = self.gcd(a,b)
        self.a /= x
        self.b /= x
    @staticmethod
    def gcd(a, b):
        while b > 0:
            r = a % b
            a = b
            b = r
        return a


    def __str__(self):
        return "%d%d" %(self.a,self.b)


