import sys


class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def unique_consecutive(head):
    cur = head
    while cur and cur.next:
        if cur.val == cur.next.val:
            cur.next = cur.next.next
        else:
            cur = cur.next
    return head


def main():
    input = sys.stdin.readline
    n = int(input())
    dummy = Node('')
    cur = dummy
    for _ in range(n):
        cur.next = Node(input().strip())
        cur = cur.next
    head = dummy.next

    head = unique_consecutive(head)

    out = []
    while head:
        out.append(head.val)
        head = head.next
    print(len(out))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
