import bisect
import sys


def main():
    input = sys.stdin.readline
    n = int(input())
    a = list(map(int, input().split()))
    a.sort()
    pref = [0]
    for x in a:
        pref.append(pref[-1] + x)
    p = int(input())
    for _ in range(p):
        power = int(input())
        cnt = bisect.bisect_right(a, power)
        print(cnt, pref[cnt])


if __name__ == "__main__":
    main()
