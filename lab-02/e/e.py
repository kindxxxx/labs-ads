import sys


class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def delete_middle(head, n):
    mid = n // 2
    if mid == 0:
        return head.next
    cur = head
    for _ in range(mid - 1):
        cur = cur.next
    cur.next = cur.next.next
    return head


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

    head = delete_middle(head, n)

    out = []
    while head:
        out.append(head.val)
        head = head.next
    print(' '.join(out))


if __name__ == '__main__':
    main()
