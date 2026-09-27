import sys


def main():
    input = sys.stdin.readline
    t = int(input())
    vals = list(map(int, input().split()))
    n, m = map(int, input().split())
    a = [list(map(int, input().split())) for _ in range(n)]

    pos = {}
    for i in range(n):
        row = a[i]
        for j in range(m):
            pos[row[j]] = (i, j)

    out = []
    for v in vals:
        p = pos.get(v)
        out.append(f"{p[0]} {p[1]}" if p else "-1")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
