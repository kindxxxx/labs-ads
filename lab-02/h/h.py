class Node:
    def __init__(self, val):
        self.val = val
        self.next = None


def max_subarray(head):
    best = cur_sum = head.val
    head = head.next
    while head:
        if cur_sum > 0:
            cur_sum += head.val
        else:
            cur_sum = head.val
        if cur_sum > best:
            best = cur_sum
        head = head.next
    return best


def main():
    n = int(input())
    vals = list(map(int, input().split()))

    dummy = Node(0)
    cur = dummy
    for v in vals:
        cur.next = Node(v)
        cur = cur.next
    head = dummy.next

    print(max_subarray(head))


if __name__ == '__main__':
    main()
