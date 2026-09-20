import sys


class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def merge(a, b):
    dummy = Node(0)
    cur = dummy
    while a and b:
        if a.val <= b.val:
            cur.next = a
            a = a.next
        else:
            cur.next = b
            b = b.next
        cur = cur.next
    cur.next = a if a else b
    return dummy.next


def build(vals):
    dummy = Node(0)
    cur = dummy
    for v in vals:
        cur.next = Node(int(v))
        cur = cur.next
    return dummy.next


def main():
    input = sys.stdin.readline
    line1 = input().split()
    line2 = input().split()
    a = build(line1[1:])
    b = build(line2[1:])

    head = merge(a, b)

    out = []
    while head:
        out.append(str(head.val))
        head = head.next
    print(' '.join(out))


if __name__ == '__main__':
    main()
