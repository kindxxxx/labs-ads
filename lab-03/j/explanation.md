# J. Задача J

## Условие

Задача J

## Алгоритм

Бинарный поиск по стороне квадрата: сколько пастбищ полностью влезает в квадрат [0,L]×[0,L].

## Код

```python
import sys


def main():
    input = sys.stdin.readline
    n, k = map(int, input().split())
    rects = []
    max_side = 0
    for _ in range(n):
        x1, y1, x2, y2 = map(int, input().split())
        rects.append((x2, y2))
        max_side = max(max_side, x2, y2)

    def count(side):
        return sum(1 for x2, y2 in rects if x2 <= side and y2 <= side)

    lo, hi = 1, max_side
    while lo < hi:
        mid = (lo + hi) // 2
        if count(mid) >= k:
            hi = mid
        else:
            lo = mid + 1
    print(lo)


if __name__ == "__main__":
    main()
```
