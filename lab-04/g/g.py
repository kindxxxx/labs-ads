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


def count_less(node: Node | None, key: int) -> int:
    if not node:
        return 0
    if key <= node.key:
        return count_less(node.left, key)
    left_size = node.left.size if node.left else 0
    return left_size + 1 + count_less(node.right, key)


def main() -> None:
    it = iter(map(int, sys.stdin.read().split()))
    n = next(it)
    root = None
    for _ in range(n):
        root = insert(root, next(it))
    q = next(it)
    out = [str(count_less(root, next(it))) for _ in range(q)]
    print("\n".join(out))


if __name__ == "__main__":
    main()
