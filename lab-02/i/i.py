import sys


class Node:
    def __init__(self, val):
        self.val = val
        self.prev = None
        self.next = None


def main():
    head = None
    tail = None
    out = []

    for line in sys.stdin:
        parts = line.split()
        if not parts:
            continue
        cmd = parts[0]

        if cmd == 'exit':
            out.append('goodbye')
            break

        if cmd == 'add_front':
            node = Node(parts[1])
            node.next = head
            if head:
                head.prev = node
            else:
                tail = node
            head = node
            out.append('ok')

        elif cmd == 'add_back':
            node = Node(parts[1])
            node.prev = tail
            if tail:
                tail.next = node
            else:
                head = node
            tail = node
            out.append('ok')

        elif cmd == 'erase_front':
            if head is None:
                out.append('error')
            else:
                out.append(head.val)
                head = head.next
                if head:
                    head.prev = None
                else:
                    tail = None

        elif cmd == 'erase_back':
            if tail is None:
                out.append('error')
            else:
                out.append(tail.val)
                tail = tail.prev
                if tail:
                    tail.next = None
                else:
                    head = None

        elif cmd == 'front':
            out.append(head.val if head else 'error')

        elif cmd == 'back':
            out.append(tail.val if tail else 'error')

        elif cmd == 'clear':
            head = None
            tail = None
            out.append('ok')

    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
