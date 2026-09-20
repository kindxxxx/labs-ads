class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def delete_every_second(head):
    cur = head
    while cur and cur.next:
        cur.next = cur.next.next
        cur = cur.next
    return head


def main():
    n = int(input())
    vals = list(map(int, input().split()))

    dummy = Node(0)
    cur = dummy
    for v in vals:
        cur.next = Node(v)
        cur = cur.next
    head = dummy.next

    head = delete_every_second(head)

    out = []
    while head:
        out.append(str(head.val))
        head = head.next
    print(' '.join(out))


if __name__ == '__main__':
    main()
