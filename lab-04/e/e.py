import sys
from collections import deque


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


def main() -> None:
    it = iter(map(int, sys.stdin.read().split()))
    n = next(it)
    root = None
    for _ in range(n):
        root = insert(root, next(it))

    ans = 0
    q = deque([root])
    while q:
        ans = max(ans, len(q))
        for _ in range(len(q)):
            node = q.popleft()
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
    print(ans)


if __name__ == "__main__":
    main()
