def main():
    n, h = map(int, input().split())
    bags = list(map(int, input().split()))

    def ok(k):
        return sum((b + k - 1) // k for b in bags) <= h

    lo, hi = 1, max(bags)
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    print(lo)


if __name__ == "__main__":
    main()
