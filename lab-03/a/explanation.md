# A. Задача A

## Условие

Задача A

## Алгоритм

Классический бинарный поиск: `bisect_left` находит позицию x в отсортированном массиве.

## Код

```python
import bisect


def main():
    n = int(input())
    a = list(map(int, input().split()))
    x = int(input())
    i = bisect.bisect_left(a, x)
    print("Yes" if i < n and a[i] == x else "No")


if __name__ == "__main__":
    main()
```
