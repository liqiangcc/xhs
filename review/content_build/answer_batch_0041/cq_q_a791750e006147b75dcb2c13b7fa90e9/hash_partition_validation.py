from collections import defaultdict

MASK = (1 << 64) - 1


def fnv1a64(value: str) -> int:
    h = 1469598103934665603
    for byte in value.encode("utf-8"):
        h ^= byte
        h = (h * 1099511628211) & MASK
    return h


def partition(values, k):
    buckets = defaultdict(list)
    for value in values:
        buckets[fnv1a64(value) % k].append(value)
    return buckets


def exact_intersection(left, right, k):
    left_buckets = partition(left, k)
    right_buckets = partition(right, k)
    result = set()
    for index in range(k):
        a = left_buckets[index]
        b = right_buckets[index]
        smaller, other = (a, b) if len(a) <= len(b) else (b, a)
        exact = set(smaller)
        for value in other:
            if value in exact:
                result.add(value)
    return result, left_buckets, right_buckets


left = [
    "https://a.example/x",
    "https://dup.example/1",
    "https://only-a.example",
    "https://dup.example/2",
    "https://dup.example/1",
    "https://same-bucket.example/a",
]
right = [
    "https://dup.example/2",
    "https://only-b.example",
    "https://dup.example/1",
    "https://dup.example/2",
    "https://c.example/y",
    "https://same-bucket.example/b",
]

k = 4
result, left_buckets, right_buckets = exact_intersection(left, right, k)
expected = {"https://dup.example/1", "https://dup.example/2"}
assert result == expected, (result, expected)

for value in expected:
    bucket = fnv1a64(value) % k
    assert value in left_buckets[bucket]
    assert value in right_buckets[bucket]

collision_pair = None
for a in left:
    for b in right:
        if a != b and fnv1a64(a) % k == fnv1a64(b) % k:
            collision_pair = (a, b, fnv1a64(a) % k)
            break
    if collision_pair:
        break

assert collision_pair is not None
assert collision_pair[0] != collision_pair[1]
print(
    "PASS exact-intersection=2 duplicates-deduped "
    "same-url-same-bucket collision-does-not-match"
)
