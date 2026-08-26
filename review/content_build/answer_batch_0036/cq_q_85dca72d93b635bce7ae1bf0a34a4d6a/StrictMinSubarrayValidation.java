import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
import java.util.Random;

public final class StrictMinSubarrayValidation {
    static int solve(long target, int[] nums) {
        int n = nums.length;
        long[] prefix = new long[n + 1];
        for (int i = 0; i < n; i++) prefix[i + 1] = prefix[i] + nums[i];
        int best = n + 1;
        Deque<Integer> deque = new ArrayDeque<>();
        for (int j = 0; j <= n; j++) {
            while (!deque.isEmpty() && prefix[j] - prefix[deque.peekFirst()] > target) {
                best = Math.min(best, j - deque.removeFirst());
            }
            while (!deque.isEmpty() && prefix[j] <= prefix[deque.peekLast()]) deque.removeLast();
            deque.addLast(j);
        }
        return best == n + 1 ? 0 : best;
    }

    static int oracle(long target, int[] nums) {
        int best = nums.length + 1;
        for (int i = 0; i < nums.length; i++) {
            long sum = 0;
            for (int j = i; j < nums.length; j++) {
                sum += nums[j];
                if (sum > target) best = Math.min(best, j - i + 1);
            }
        }
        return best == nums.length + 1 ? 0 : best;
    }

    static int nonnegativeWindow(long target, int[] nums) {
        int best = nums.length + 1, left = 0;
        long sum = 0;
        for (int right = 0; right < nums.length; right++) {
            if (nums[right] < 0) throw new IllegalArgumentException("nonnegative only");
            sum += nums[right];
            while (left <= right && sum > target) {
                best = Math.min(best, right - left + 1);
                sum -= nums[left++];
            }
        }
        return best == nums.length + 1 ? 0 : best;
    }

    static void check(long target, int[] input, int expected) {
        int actual = solve(target, input);
        if (actual != expected) throw new AssertionError("target="+target+" input="+Arrays.toString(input)+" expected="+expected+" actual="+actual);
    }

    public static void main(String[] args) {
        check(7, new int[]{7}, 0);
        check(7, new int[]{8}, 1);
        check(7, new int[]{2,3,1,2,4,3}, 3); // 4+3 equals 7, so strict solution is length 3
        check(3, new int[]{2,-1,2,2}, 2);
        check(3, new int[]{5,-10,5}, 1);
        check(0, new int[]{-1,0,1}, 1);
        check(10, new int[]{}, 0);
        check(-2, new int[]{-3,-1}, 1);
        check(4, new int[]{2,2}, 0);
        check(4, new int[]{2,2,1}, 3);

        Random r = new Random(2026082603L);
        long checked = 0;
        for (int round=0; round<7000; round++) {
            int n=r.nextInt(45);
            int[] a=new int[n];
            for(int i=0;i<n;i++) a[i]=-20+r.nextInt(41);
            long target=-30+r.nextInt(91);
            int expected=oracle(target,a), actual=solve(target,a);
            if(expected!=actual) throw new AssertionError("general round="+round+" target="+target+" input="+Arrays.toString(a)+" expected="+expected+" actual="+actual);
            checked += n;
        }

        Random p = new Random(2026082604L);
        for (int round=0; round<3000; round++) {
            int n=p.nextInt(70);
            int[] a=new int[n];
            for(int i=0;i<n;i++) a[i]=p.nextInt(21);
            long target=p.nextInt(150);
            int expected=oracle(target,a), window=nonnegativeWindow(target,a);
            if(expected!=window) throw new AssertionError("nonnegative round="+round+" target="+target+" input="+Arrays.toString(a)+" expected="+expected+" window="+window);
        }
        System.out.println("PASS fixed=10 general-randomized=7000 nonnegative-window-randomized=3000 strict-greater=true negatives=true equality-boundary=true empty=true checked-elements="+checked);
    }
}
