# __*__ coding=utf-8 __*__

from collections import deque

#q = deque()
#q.append(1)
#print(q.popleft())


def tail(n):
    with open('text.txt', 'r') as f:
        q = deque(f,n)
        return q

for line in tail(5):
    print(line,end='')