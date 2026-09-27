import sys


def main():
    input = sys.stdin.readline
    n, k = map(int, input().split())
    a = list(map(int, input().split()))
    pref = [0]
    for x in a:
        pref.append(pref[-1] + x)

    ans = n + 1
    for l in range(n):
        lo, hi = l, n - 1
        best = n + 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if pref[mid + 1] - pref[l] >= k:
                best = mid - l + 1
                hi = mid - 1
            else:
                lo = mid + 1
        ans = min(ans, best)
    print(ans)


if __name__ == "__main__":
    main()
