import java.util.*;

public class writer_validation {
    static final class RandomSet<T> {
        private final ArrayList<T> values = new ArrayList<>();
        private final HashMap<T, Integer> index = new HashMap<>();
        private final Random random;

        RandomSet(Random random) {
            this.random = Objects.requireNonNull(random);
        }

        boolean set(T value) {
            if (index.containsKey(value)) return false;
            index.put(value, values.size());
            values.add(value);
            return true;
        }

        boolean remove(T value) {
            Integer pos = index.remove(value);
            if (pos == null) return false;
            int lastIndex = values.size() - 1;
            T last = values.get(lastIndex);
            if (pos != lastIndex) {
                values.set(pos, last);
                index.put(last, pos);
            }
            values.remove(lastIndex);
            return true;
        }

        boolean contains(T value) {
            return index.containsKey(value);
        }

        T randomGet() {
            if (values.isEmpty()) throw new NoSuchElementException("RandomSet is empty");
            return values.get(random.nextInt(values.size()));
        }

        int size() { return values.size(); }

        void assertInternalInvariant() {
            if (values.size() != index.size()) throw new AssertionError("size mismatch");
            for (int i = 0; i < values.size(); i++) {
                Integer mapped = index.get(values.get(i));
                if (mapped == null || mapped != i) throw new AssertionError("index mismatch at " + i);
            }
        }
    }

    public static void main(String[] args) {
        RandomSet<Integer> set = new RandomSet<>(new Random(0x9694af9aL));
        HashSet<Integer> oracle = new HashSet<>();
        Random ops = new Random(0x51e7L);

        if (!set.set(10) || !set.set(20) || set.set(10)) throw new AssertionError("set semantics");
        oracle.add(10); oracle.add(20);
        if (!set.contains(10) || set.contains(30)) throw new AssertionError("contains semantics");
        if (!set.remove(10) || set.remove(10) || set.contains(10)) throw new AssertionError("remove semantics");
        oracle.remove(10);
        set.assertInternalInvariant();

        int operations = 100000;
        int randomReads = 0;
        for (int t = 0; t < operations; t++) {
            int value = ops.nextInt(401) - 200;
            switch (ops.nextInt(4)) {
                case 0 -> {
                    boolean actual = set.set(value), expected = oracle.add(value);
                    if (actual != expected) throw new AssertionError("set differential");
                }
                case 1 -> {
                    boolean actual = set.remove(value), expected = oracle.remove(value);
                    if (actual != expected) throw new AssertionError("remove differential");
                }
                case 2 -> {
                    if (set.contains(value) != oracle.contains(value)) throw new AssertionError("contains differential");
                }
                default -> {
                    if (oracle.isEmpty()) {
                        boolean threw = false;
                        try { set.randomGet(); } catch (NoSuchElementException e) { threw = true; }
                        if (!threw) throw new AssertionError("empty randomGet must throw");
                    } else {
                        Integer got = set.randomGet();
                        if (!oracle.contains(got)) throw new AssertionError("randomGet returned non-member " + got);
                        randomReads++;
                    }
                }
            }
            if (set.size() != oracle.size()) throw new AssertionError("size differential");
            if ((t & 255) == 0) set.assertInternalInvariant();
        }
        set.assertInternalInvariant();

        RandomSet<Integer> swap = new RandomSet<>(new Random(1));
        swap.set(1); swap.set(2); swap.set(3); swap.set(4);
        if (!swap.remove(2) || swap.contains(2) || swap.size() != 3) throw new AssertionError("swap-delete");
        swap.assertInternalInvariant();
        for (int i = 0; i < 1000; i++) {
            int got = swap.randomGet();
            if (got == 2 || !(got == 1 || got == 3 || got == 4)) throw new AssertionError("swap random membership");
        }

        RandomSet<Integer> empty = new RandomSet<>(new Random(2));
        boolean threw = false;
        try { empty.randomGet(); } catch (NoSuchElementException e) { threw = true; }
        if (!threw) throw new AssertionError("empty behavior");

        System.out.println("PASS deterministic=swap-delete randomized-operations=" + operations + " random-member-reads=" + randomReads + " invariant=index-bijection empty=randomGet-throws");
    }
}
