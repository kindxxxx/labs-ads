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

    q = deque([(root, 0)])
    best_d = 0
    level_sum = 0
    while q:
        node, d = q.popleft()
        if d > best_d:
            best_d = d
            level_sum = 0
        if d == best_d:
            level_sum += node.key
        if node.left:
            q.append((node.left, d + 1))
        if node.right:
            q.append((node.right, d + 1))
    print(level_sum)


if __name__ == "__main__":
    main()
