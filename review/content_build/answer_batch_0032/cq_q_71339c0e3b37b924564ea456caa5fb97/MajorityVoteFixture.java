import java.util.HashMap;
import java.util.Map;
import java.util.OptionalInt;
import java.util.Random;

public final class MajorityVoteFixture {
    static OptionalInt actual(int[] nums) {
        if (nums == null || nums.length == 0) return OptionalInt.empty();
        int candidate = 0, count = 0;
        for (int value : nums) {
            if (count == 0) { candidate = value; count = 1; }
            else if (value == candidate) count++;
            else count--;
        }
        int occurrences = 0;
        for (int value : nums) if (value == candidate) occurrences++;
        return occurrences > nums.length / 2 ? OptionalInt.of(candidate) : OptionalInt.empty();
    }

    static OptionalInt oracle(int[] nums) {
        if (nums == null || nums.length == 0) return OptionalInt.empty();
        Map<Integer,Integer> counts = new HashMap<>();
        for (int v : nums) counts.merge(v, 1, Integer::sum);
        for (Map.Entry<Integer,Integer> e : counts.entrySet()) if (e.getValue() > nums.length / 2) return OptionalInt.of(e.getKey());
        return OptionalInt.empty();
    }

    static void check(int[] a) {
        OptionalInt x=actual(a), y=oracle(a);
        if (!x.equals(y)) throw new AssertionError("actual="+x+" oracle="+y);
    }

    public static void main(String[] args) {
        check(null); check(new int[]{}); check(new int[]{7}); check(new int[]{2,2,1,1,1,2,2});
        check(new int[]{1,1,2,2}); check(new int[]{1,2,3}); check(new int[]{-1,-1,-1,2,3});
        Random r=new Random(71339L);
        for(int t=0;t<20000;t++){
            int n=r.nextInt(80); int[] a=new int[n];
            for(int i=0;i<n;i++) a[i]=r.nextInt(9)-4;
            check(a);
        }
        System.out.println("PASS fixed-boundaries randomized=20000 oracle=HashMap strict-majority-only");
    }
}
