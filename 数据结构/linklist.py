# __*__ coding=utf-8 __*__

class Node:
    def __init__(self,item):
        self.item = item
        self.next = None

def create_linklist(li):
    head = Node(li[0])
    for element in li[1:]:
        node = Node(element)
        node.next = head
        head = node

    return head
def print_linklist(lk):
    while lk:
        print(lk.item,end=',')
        lk = lk.next
lk = create_linklist([1,2,3])
print_linklist(lk)
print(lk.item)

