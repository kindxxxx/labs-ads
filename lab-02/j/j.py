import sys


class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def insert(head, x, p):
    node = Node(x)
    if p == 0:
        node.next = head
        return node
    cur = head
    for _ in range(p - 1):
        cur = cur.next
    node.next = cur.next
    cur.next = node
    return head


def remove(head, p):
    if p == 0:
        return head.next
    cur = head
    for _ in range(p - 1):
        cur = cur.next
    cur.next = cur.next.next
    return head


def replace(head, p1, p2):
    cur = head
    for _ in range(p1):
        cur = cur.next
    x = cur.val
    head = remove(head, p1)
    return insert(head, x, p2)


def reverse_list(head):
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


def cyclic_left(head, x):
    if head is None or x == 0:
        return head
    prev = None
    cur = head
    for _ in range(x):
        prev = cur
        cur = cur.next
    prev.next = None
    tail = cur
    while tail.next:
        tail = tail.next
    tail.next = head
    return cur


def cyclic_right(head, x):
    if head is None or x == 0:
        return head
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    return cyclic_left(head, n - x)


def print_list(head):
    if head is None:
        print(-1)
        return
    out = []
    while head:
        out.append(str(head.val))
        head = head.next
    print(' '.join(out))


def main():
    head = None
    for line in sys.stdin:
        parts = line.split()
        if not parts:
            continue
        cmd = int(parts[0])
        if cmd == 0:
            break
        elif cmd == 1:
            head = insert(head, int(parts[1]), int(parts[2]))
        elif cmd == 2:
            head = remove(head, int(parts[1]))
        elif cmd == 3:
            print_list(head)
        elif cmd == 4:
            head = replace(head, int(parts[1]), int(parts[2]))
        elif cmd == 5:
            head = reverse_list(head)
        elif cmd == 6:
            head = cyclic_left(head, int(parts[1]))
        elif cmd == 7:
            head = cyclic_right(head, int(parts[1]))


if __name__ == '__main__':
    main()
