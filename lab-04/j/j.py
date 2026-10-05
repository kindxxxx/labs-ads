import sys


class Node:
    __slots__ = ("key", "left", "right", "size")

    def __init__(self, key: int):
        self.key = key
        self.left = self.right = None
        self.size = 1


def upd(node: Node) -> None:
    node.size = 1 + (node.left.size if node.left else 0) + (node.right.size if node.right else 0)


def insert(node: Node | None, key: int) -> Node:
    if node is None:
        return Node(key)
    if key < node.key:
        node.left = insert(node.left, key)
    else:
        node.right = insert(node.right, key)
    upd(node)
    return node


def kth(node: Node, k: int) -> int:
    left_size = node.left.size if node.left else 0
    if k <= left_size:
        return kth(node.left, k)
    if k == left_size + 1:
        return node.key
    return kth(node.right, k - left_size - 1)


def main() -> None:
    it = iter(map(int, sys.stdin.read().split()))
    n = next(it)
    root = None
    for _ in range(n):
        root = insert(root, next(it))
    k = next(it)
    print(kth(root, k))


if __name__ == "__main__":
    main()
