import sys


class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def reverse_list(head):
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


def main():
    input = sys.stdin.readline
    n = int(input())
    vals = input().split()

    dummy = Node(0)
    cur = dummy
    for v in vals:
        cur.next = Node(v)
        cur = cur.next
    head = dummy.next

    head = reverse_list(head)

    out = []
    while head:
        out.append(head.val)
        head = head.next
    print(' '.join(out))


if __name__ == '__main__':
    main()
