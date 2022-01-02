# __*__ coding=utf-8 __*__
import random
def bubble_sort(li):
    for i in range(len(li)- 1):
        exchange = False
        for j in range(len(li) - 1):
            if li[j] > li[j+1]:
                li[j],li[j+1]=li[j+1],li[j]
                exchange = True
        print(li)
        if not exchange:
            return

#li = [random.randint(0,100) for i in range(100)]
li = [1,2,3]
print(li)
bubble_sort(li)
print('end')