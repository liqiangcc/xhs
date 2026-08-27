import random

def consume(weights, left_budget, right_budget):
    # weights are arbitrary positive one-end burn-time chunks summing to 60.
    a=list(weights); i=0; j=len(a)-1; li=a[i] if a else 0.0; rj=a[j] if a else 0.0
    l=left_budget; r=right_budget
    while i<=j and l>1e-9:
        take=min(li,l); li-=take; l-=take
        if li<=1e-9: i+=1; li=a[i] if i<=j else 0.0
    while i<=j and r>1e-9:
        take=min(rj,r); rj-=take; r-=take
        if rj<=1e-9: j-=1; rj=a[j] if i<=j else 0.0
    rem=0.0
    if i>j: return 0.0
    if i==j: return max(0.0, li - (a[i]-rj))
    rem=li+rj+sum(a[i+1:j])
    return rem

assert 60/2 == 30
assert (60-30)/2 == 15
rng=random.Random(0x524f504531354d)
for _ in range(20000):
    n=rng.randint(1,25)
    cuts=sorted([0.0]+[rng.random() for _ in range(n-1)]+[1.0])
    weights=[(cuts[k+1]-cuts[k])*60.0 for k in range(n)]
    # B burns from one end for 30 real minutes -> 30 units remain, independent of partition.
    rem=consume(weights,30.0,0.0)
    if abs(rem-30.0)>1e-7: raise AssertionError((weights,rem))
    # Once both ends are lit, two one-end-time units disappear per real minute -> 15 minutes.
    if abs(rem/2.0-15.0)>1e-7: raise AssertionError(rem)
print('PASS total=60 first-marker=30 remaining-B=30 measured-interval=15 random-irregular-partitions=20000')
