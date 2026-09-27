# G. Задача G

## Условие

Задача G

## Алгоритм

Бинарный поиск по длине куска L: сколько кусков получится из всех верёvok. Нужно >= k.

## Код

```python
def main():
    n, k = map(int, input().split())
    a = list(map(int, input().split()))

    def pieces(length):
        return sum(int(x / length) for x in a)

    lo, hi = 0.0, float(max(a))
    for _ in range(100):
        mid = (lo + hi) / 2
        if pieces(mid) >= k:
            lo = mid
        else:
            hi = mid
    print(f"{lo:.9f}")


if __name__ == "__main__":
    main()
```
