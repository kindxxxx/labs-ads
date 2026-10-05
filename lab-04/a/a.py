import sys


class BIT:
    def __init__(self, n: int):
        self.n = n
        self.t = [0] * (n + 1)

    def add(self, i: int, v: int = 1) -> None:
        i += 1
        while i <= self.n:
            self.t[i] += v
            i += i & -i

    def sum(self, i: int) -> int:
        i += 1
        s = 0
        while i:
            s += self.t[i]
            i -= i & -i
        return s


def main() -> None:
    data = list(map(int, sys.stdin.read().split()))
    n = data[0]
    h = data[1 : 1 + n]
    vals = sorted(set(h))
    comp = {v: i for i, v in enumerate(vals)}
    m = len(vals)

    left = [0] * n
    bit = BIT(m)
    for i, x in enumerate(h):
        c = comp[x]
        left[i] = bit.sum(c - 1)
        bit.add(c)

    right = [0] * n
    bit = BIT(m)
    for i in range(n - 1, -1, -1):
        c = comp[h[i]]
        right[i] = bit.sum(c - 1)
        bit.add(c)

    print(sum(left[i] * right[i] for i in range(n)))


if __name__ == "__main__":
    main()
