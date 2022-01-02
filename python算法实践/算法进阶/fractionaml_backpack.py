# -*- coding: utf-8 -*-
'''
@Time    : 2021/1/5 4:56 下午
@Author  : chenbokai
@File    : fractionaml_backpack.py
'''


goods = [(60,10),(100,20),(120,30)] # 商品（价格，重量）
goods.sort(key=lambda x:x[0]/x[1],reverse=True)

def fractional_backpack(goods,w):
    m = [0 for _ in range(len(goods))]
    total_v = 0
    for i ,(price,weight) in enumerate(goods):
        if w>=weight:
            m[i] = 1
            w -= weight
            total_v += price
        else:
            m[i] = w / weight
            w = 0
            total_v += m[i] * price
            break
    return total_v,m


print(fractional_backpack(goods,50))