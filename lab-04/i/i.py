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


def inorder_nodes(root: Node | None, out: list[Node]) -> None:
    if not root:
        return
    inorder_nodes(root.left, out)
    out.append(root)
    inorder_nodes(root.right, out)


def recover(root: Node | None) -> None:
    first = second = prev = None
    cur = root
    while cur:
        if cur.left:
            pred = cur.left
            while pred.right and pred.right != cur:
                pred = pred.right
            if not pred.right:
                pred.right = cur
                cur = cur.left
            else:
                pred.right = None
                if prev and prev.key > cur.key:
                    if first is None:
                        first = prev
                    second = cur
                prev = cur
                cur = cur.right
        else:
            if prev and prev.key > cur.key:
                if first is None:
                    first = prev
                second = cur
            prev = cur
            cur = cur.right
    if first and second:
        first.key, second.key = second.key, first.key


def main() -> None:
    it = iter(map(int, sys.stdin.read().split()))
    n = next(it)
    root = None
    for _ in range(n):
        root = insert(root, next(it))
    recover(root)
    nodes: list[Node] = []
    inorder_nodes(root, nodes)
    print(" ".join(str(x.key) for x in nodes))


if __name__ == "__main__":
    main()
