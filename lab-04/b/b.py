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
    elif key > root.key:
        root.right = insert(root.right, key)
    return root


def search(root: Node | None, key: int) -> Node | None:
    while root:
        if key == root.key:
            return root
        root = root.left if key < root.key else root.right
    return None


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
    v = next(it)
    sub = search(root, v)
    if sub:
        out: list[str] = []
        inorder(sub, out)
        print(" ".join(out))


if __name__ == "__main__":
    main()
