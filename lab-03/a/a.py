import bisect


def main():
    n = int(input())
    a = list(map(int, input().split()))
    x = int(input())
    i = bisect.bisect_left(a, x)
    print("Yes" if i < n and a[i] == x else "No")


if __name__ == "__main__":
    main()
