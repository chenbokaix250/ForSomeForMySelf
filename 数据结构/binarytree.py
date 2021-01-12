# __*__ coding=utf-8 __*__
from collections import deque
class BiTreeNode:
    def __init__(self,data):
        self.data = data
        self.lchild = None
        self.rchild = None

a = BiTreeNode("A")
b = BiTreeNode("B")
c = BiTreeNode("C")
d = BiTreeNode("D")
e = BiTreeNode("E")
f = BiTreeNode("F")
g = BiTreeNode("G")

e.lchild = a
e.rchild = g
a.rchild = c
c.lchild = b
c.rchild = d
g.rchild = f

root = e
print(root.lchild.rchild.data)


def pre_order(root):
    if root:
        print(root.data,end=",")
        pre_order(root.lchild)
        pre_order(root.rchild)
#pre_order(root)

def in_order(root):
    if root:
        in_order(root.lchild)
        print(root.data,end=",")
        in_order(root.rchild)
#in_order(root)
def post_order(root):
    if root:
        post_order(root.lchild)
        post_order(root.rchild)
        print(root.data,end=",")
#post_order(root)

def level_order(root):
    queue = deque()
    queue.append(root)
    while len(queue) > 0:
        node = queue.popleft()
        print(node.data,end=",")
        if node.lchild:
            queue.append(node.lchild)
        if node.rchild:
            queue.append(node.rchild)
#level_order(root)


