import bisect
import sys


def count_in(a, l, r):
    return bisect.bisect_right(a, r) - bisect.bisect_left(a, l)


def main():
    input = sys.stdin.readline
    n, q = map(int, input().split())
    a = list(map(int, input().split()))
    a.sort()
    for _ in range(q):
        l1, r1, l2, r2 = map(int, input().split())
        c1 = count_in(a, l1, r1)
        c2 = count_in(a, l2, r2)
        lo = max(l1, l2)
        hi = min(r1, r2)
        overlap = count_in(a, lo, hi) if lo <= hi else 0
        print(c1 + c2 - overlap)


if __name__ == "__main__":
    main()
