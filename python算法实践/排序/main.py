# __*__ coding=utf-8 __*__

from 排序.cal_time import *
@cal_time
def linear_search(li,val):
    for ind,v in enumerate(li):
        if v == val:
            return ind
        else:
            return None

@cal_time
def binary_search(li,val):
    left = 0
    right = len(li) - 1
    while left <= right:
        mid = (left + right) // 2
        if li[mid] == val:
            return mid
        elif li[mid] > val:
            right = mid - 1
        elif li[mid] < val:
            left = mid + 1
    else:
        return None

li = list(range(10000000))
binary_search(li,989000)
linear_search(li,989000)

