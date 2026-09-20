from collections import Counter, deque


def first_unique(letters):
    cnt = Counter()
    q = deque()
    ans = []
    for ch in letters:
        cnt[ch] += 1
        if cnt[ch] == 1:
            q.append(ch)
        while q and cnt[q[0]] > 1:
            q.popleft()
        ans.append(q[0] if q else '-1')
    return ans


def main():
    t = int(input())
    for _ in range(t):
        input()
        letters = input().split()
        print(' '.join(first_unique(letters)))


if __name__ == '__main__':
    main()
