import sys


class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def rotate_left(head, k):
    cur = head
    for _ in range(k - 1):
        cur = cur.next
    new_head = cur.next
    cur.next = None
    tail = new_head
    while tail.next:
        tail = tail.next
    tail.next = head
    return new_head


def main():
    input = sys.stdin.readline
    n, k = map(int, input().split())
    words = input().split()

    dummy = Node('')
    cur = dummy
    for w in words:
        cur.next = Node(w)
        cur = cur.next
    head = dummy.next

    head = rotate_left(head, k)

    out = []
    while head:
        out.append(head.val)
        head = head.next
    print(' '.join(out))


if __name__ == '__main__':
    main()
