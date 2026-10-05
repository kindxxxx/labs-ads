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


def inorder(node: Node | None, out: list[int]) -> None:
    if not node:
        return
    inorder(node.left, out)
    out.append(node.key)
    inorder(node.right, out)


def count_triangles(arr: list[int]) -> int:
    arr.sort()
    n = len(arr)
    ans = 0
    for i in range(n - 2):
        k = i + 2
        for j in range(i + 1, n - 1):
            while k < n and arr[i] + arr[j] > arr[k]:
                k += 1
            ans += k - j - 1
    return ans


def main() -> None:
    it = iter(map(int, sys.stdin.read().split()))
    n = next(it)
    root = None
    for _ in range(n):
        root = insert(root, next(it))
    vals: list[int] = []
    inorder(root, vals)
    print(count_triangles(vals))


if __name__ == "__main__":
    main()
