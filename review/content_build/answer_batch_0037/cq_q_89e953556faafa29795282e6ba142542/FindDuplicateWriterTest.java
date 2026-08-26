import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public final class FindDuplicateWriterTest {
    public static void main(String[] args) {
        Solution s=new Solution();
        check(s,new int[]{1,3,4,2,2},2);
        check(s,new int[]{3,1,3,4,2},3);
        check(s,new int[]{3,3,3,3,3},3);
        check(s,new int[]{1,1},1);
        check(s,new int[]{2,1,2},2);
        Random r=new Random(0x287L);
        int cases=0;
        for(int n=2;n<=120;n++) for(int round=0;round<20;round++) {
            int duplicate=1+r.nextInt(n);
            List<Integer> values=new ArrayList<>();
            for(int v=1;v<=n;v++) values.add(v);
            values.add(duplicate);
            Collections.shuffle(values,r);
            int[] nums=values.stream().mapToInt(Integer::intValue).toArray();
            int[] before=nums.clone();
            check(s,nums,duplicate);
            if(!java.util.Arrays.equals(nums,before)) throw new AssertionError("input mutated");
            cases++;
        }
        System.out.printf("PASS official_examples=3 boundaries=2 random_valid_cases=%d input_unchanged=pass multi_occurrence=pass%n",cases);
    }
    private static void check(Solution s,int[] nums,int expected) {
        int actual=s.findDuplicate(nums);
        if(actual!=expected) throw new AssertionError("actual="+actual+" expected="+expected+" nums="+java.util.Arrays.toString(nums));
    }
}
