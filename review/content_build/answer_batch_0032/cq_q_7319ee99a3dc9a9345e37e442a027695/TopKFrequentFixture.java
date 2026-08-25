import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Random;

public final class TopKFrequentFixture {
    record Entry(int value, int frequency) {}

    static List<Integer> actual(int[] nums, int k) {
        if (nums == null) throw new NullPointerException("nums");
        Map<Integer,Integer> f = new HashMap<>();
        for (int v : nums) f.merge(v, 1, Integer::sum);
        if (k <= 0 || k > f.size()) throw new IllegalArgumentException("k");
        Comparator<Entry> worstFirst = Comparator.comparingInt(Entry::frequency)
                .thenComparing(Comparator.comparingInt(Entry::value).reversed());
        PriorityQueue<Entry> heap = new PriorityQueue<>(worstFirst);
        for (Map.Entry<Integer,Integer> e : f.entrySet()) {
            heap.offer(new Entry(e.getKey(), e.getValue()));
            if (heap.size() > k) heap.poll();
        }
        List<Integer> out = new ArrayList<>();
        while (!heap.isEmpty()) out.add(heap.poll().value());
        Collections.reverse(out);
        return out;
    }

    static List<Integer> oracle(int[] nums, int k) {
        if (nums == null) throw new NullPointerException("nums");
        Map<Integer,Integer> f = new HashMap<>();
        for (int v : nums) f.merge(v, 1, Integer::sum);
        if (k <= 0 || k > f.size()) throw new IllegalArgumentException("k");
        List<Integer> values = new ArrayList<>(f.keySet());
        values.sort((a,b) -> {
            int byFreq = Integer.compare(f.get(b), f.get(a));
            return byFreq != 0 ? byFreq : Integer.compare(a,b);
        });
        return new ArrayList<>(values.subList(0, k));
    }

    static void check(int[] a, int k) {
        List<Integer> x = actual(a,k), y = oracle(a,k);
        if (!x.equals(y)) throw new AssertionError("actual="+x+" oracle="+y+" k="+k);
    }

    public static void main(String[] args) {
        check(new int[]{1,1,1,2,2,3}, 2);
        check(new int[]{4,4,3,3,2}, 2);
        check(new int[]{-1,-1,-2,-2,-2,7}, 2);
        check(new int[]{9}, 1);
        boolean badZero=false,badTooLarge=false,badEmpty=false;
        try { actual(new int[]{1},0); } catch (IllegalArgumentException e) { badZero=true; }
        try { actual(new int[]{1},2); } catch (IllegalArgumentException e) { badTooLarge=true; }
        try { actual(new int[]{},1); } catch (IllegalArgumentException e) { badEmpty=true; }
        if(!badZero||!badTooLarge||!badEmpty) throw new AssertionError("invalid-k contract failed");

        Random r = new Random(7319L);
        int cases = 0;
        for (int t=0; t<20000; t++) {
            int n = 1 + r.nextInt(100);
            int[] a = new int[n];
            for (int i=0;i<n;i++) a[i]=r.nextInt(21)-10;
            Map<Integer,Integer> distinct = new HashMap<>();
            for(int v:a) distinct.merge(v,1,Integer::sum);
            int k = 1 + r.nextInt(distinct.size());
            check(a,k);
            cases++;
        }
        System.out.println("PASS fixed-boundaries randomized=20000 oracle=full-sort deterministic-tie=frequency-desc-value-asc");
    }
}
