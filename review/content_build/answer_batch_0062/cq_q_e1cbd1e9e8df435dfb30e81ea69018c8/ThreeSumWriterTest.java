import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;
import java.util.TreeSet;

public final class ThreeSumWriterTest {
    private static final Random RNG = new Random(0x62E1CBD1L);

    static String key(int x, int y, int z) {
        int[] a = {x,y,z}; Arrays.sort(a);
        return a[0] + "," + a[1] + "," + a[2];
    }
    static Set<String> normalize(List<List<Integer>> rows) {
        Set<String> out = new TreeSet<>();
        for (List<Integer> row : rows) {
            if (row.size() != 3) throw new AssertionError("not a triplet: " + row);
            String k = key(row.get(0), row.get(1), row.get(2));
            if (!out.add(k)) throw new AssertionError("duplicate result triplet: " + k);
            long sum = (long) row.get(0) + row.get(1) + row.get(2);
            if (sum != 0L) throw new AssertionError("non-zero triplet: " + row);
        }
        return out;
    }
    static Set<String> oracle(int[] nums) {
        Set<String> out = new TreeSet<>();
        for (int i=0;i<nums.length;i++) for (int j=i+1;j<nums.length;j++) for (int k=j+1;k<nums.length;k++) {
            if ((long)nums[i] + nums[j] + nums[k] == 0L) out.add(key(nums[i],nums[j],nums[k]));
        }
        return out;
    }
    static void check(int[] input, Set<String> expected, String label) {
        int[] before = input.clone();
        Set<String> actual = normalize(ThreeSum.threeSum(input));
        if (!actual.equals(expected)) throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        if (!Arrays.equals(input,before)) throw new AssertionError(label + " mutated input");
    }
    static Set<String> set(String... xs) { return new TreeSet<>(Arrays.asList(xs)); }

    public static void main(String[] args) {
        check(new int[]{-1,0,1,2,-1,-4}, set("-1,-1,2","-1,0,1"), "classic");
        check(new int[]{0,0,0,0}, set("0,0,0"), "all-zero");
        check(new int[]{1,2,-2,-1}, set(), "none");
        check(new int[]{-2,0,0,2,2}, set("-2,0,2"), "dedupe-both-sides");
        check(new int[]{-4,-2,-2,-2,0,1,2,2,2,3,3,4}, oracle(new int[]{-4,-2,-2,-2,0,1,2,2,2,3,3,4}), "many-duplicates");
        check(new int[]{Integer.MIN_VALUE,1,Integer.MAX_VALUE}, set(Integer.MIN_VALUE + ",1," + Integer.MAX_VALUE), "overflow-zero");
        check(new int[]{Integer.MAX_VALUE,Integer.MAX_VALUE,2,-3,-1}, oracle(new int[]{Integer.MAX_VALUE,Integer.MAX_VALUE,2,-3,-1}), "overflow-direction");
        check(new int[]{-1,-1,-1,2,2,2}, set("-1,-1,2"), "duplicate-index-combos");
        check(new int[]{}, set(), "empty");
        if (!ThreeSum.threeSum(null).isEmpty()) throw new AssertionError("null contract");

        int cases=0;
        for (int t=0;t<20000;t++) {
            int len=RNG.nextInt(10);
            int[] input=new int[len];
            for(int i=0;i<len;i++) input[i]=RNG.nextInt(21)-10;
            int[] before=input.clone();
            Set<String> expected=oracle(input);
            Set<String> actual=normalize(ThreeSum.threeSum(input));
            if(!expected.equals(actual)) throw new AssertionError("random-"+t+" input="+Arrays.toString(input)+" expected="+expected+" actual="+actual);
            if(!Arrays.equals(input,before)) throw new AssertionError("random mutation-"+t);
            cases++;
        }
        if(cases!=20000) throw new AssertionError("case count");
        System.out.println("PASS fixed=9 random_cases=20000 oracle=bruteforce-triples overflow=pass input_unchanged=pass dedupe=pass");
    }
}
