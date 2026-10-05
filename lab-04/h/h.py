import sys


class Node:
    __slots__ = ("key", "left", "right")

    def __init__(self, key: int):
        self.key = key
        self.left = self.right = None


def insert(root: Node | None, key: int) -> Node:
    if root is None:
        return Node(key)
    if key < root.key:
        root.left = insert(root.left, key)
    else:
        root.right = insert(root.right, key)
    return root


def transform(root: Node | None, total: int) -> int:
    if not root:
        return total
    total = transform(root.right, total)
    total += root.key
    root.key = total
    return transform(root.left, total)


def inorder(node: Node | None, out: list[str]) -> None:
    if not node:
        return
    inorder(node.left, out)
    out.append(str(node.key))
    inorder(node.right, out)


def main() -> None:
    it = iter(map(int, sys.stdin.read().split()))
    n = next(it)
    root = None
    for _ in range(n):
        root = insert(root, next(it))
    transform(root, 0)
    out: list[str] = []
    inorder(root, out)
    print(" ".join(out))


if __name__ == "__main__":
    main()
