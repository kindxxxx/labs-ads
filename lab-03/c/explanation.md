# C. Задача C

## Условие

Задача C

## Алгоритм

Строим массив концов блоков. Для каждой ошибочной строки — бинарный поиск, в каком блоке она лежит.

## Код

```python
import bisect
import sys


def main():
    input = sys.stdin.readline
    n, m = map(int, input().split())
    blocks = list(map(int, input().split()))
    ends = []
    cur = 0
    for x in blocks:
        cur += x
        ends.append(cur)
    for _ in range(m):
        line = int(input())
        block = bisect.bisect_left(ends, line) + 1
        print(block)


if __name__ == "__main__":
    main()
```
