import sys
from collections import deque


def main() -> None:
    data = sys.stdin.read().split()
    it = iter(data)
    s = int(next(it))
    f = int(next(it))
    edges = []
    deg = [0] * (s + 1)
    for _ in range(f):
        a = int(next(it))
        b = int(next(it))
        edges.append((a, b))
        deg[a] += 1
        deg[b] += 1

    print(sum(1 for i in range(1, s + 1) if deg[i] % 2))

    adj: list[list[tuple[int, int]]] = [[] for _ in range(s + 1)]
    for i, (a, b) in enumerate(edges):
        adj[a].append((b, i))
        adj[b].append((a, i))

    orient: list[tuple[int, int] | None] = [None] * f
    used = [False] * f

    for start in range(1, s + 1):
        if not adj[start]:
            continue
        stack = [start]
        parent = [-1] * (s + 1)
        parent_e = [-1] * (s + 1)
        parent[start] = 0
        order: list[int] = []
        while stack:
            v = stack.pop()
            order.append(v)
            for u, ei in adj[v]:
                if used[ei]:
                    continue
                if parent[u] == -1 and u != parent[v]:
                    parent[u] = v
                    parent_e[u] = ei
                    stack.append(u)
                elif u != parent[v]:
                    used[ei] = True
                    a, b = edges[ei]
                    orient[ei] = (a, b)

        deg2 = deg[:]
        q = deque(i for i in range(1, s + 1) if deg2[i] == 1)
        while q:
            u = q.popleft()
            ei = parent_e[u]
            if ei == -1 or used[ei]:
                continue
            used[ei] = True
            p = parent[u]
            orient[ei] = (u, p)
            deg2[u] = 0
            deg2[p] -= 1
            if deg2[p] == 1:
                q.append(p)

    for i, (a, b) in enumerate(edges):
        if orient[i] is None:
            orient[i] = (a, b)
        print(orient[i][0], orient[i][1])


if __name__ == "__main__":
    main()
