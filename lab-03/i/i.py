import sys


def main():
    input = sys.stdin.readline
    n, k = map(int, input().split())
    a = list(map(int, input().split()))

    def ok(limit):
        parts = 1
        cur = 0
        for x in a:
            if x > limit:
                return False
            if cur + x > limit:
                parts += 1
                cur = x
            else:
                cur += x
        return parts <= k

    lo, hi = max(a), sum(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    print(lo)


if __name__ == "__main__":
    main()
