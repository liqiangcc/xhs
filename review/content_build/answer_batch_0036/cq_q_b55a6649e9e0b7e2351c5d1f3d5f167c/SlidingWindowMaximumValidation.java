import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
import java.util.Random;

public final class SlidingWindowMaximumValidation {
    static int[] solve(int[] nums, int k) {
        if (nums == null || k <= 0 || k > nums.length) throw new IllegalArgumentException("invalid input");
        int[] answer = new int[nums.length - k + 1];
        Deque<Integer> deque = new ArrayDeque<>();
        int out = 0;
        for (int i = 0; i < nums.length; i++) {
            while (!deque.isEmpty() && deque.peekFirst() <= i - k) deque.removeFirst();
            while (!deque.isEmpty() && nums[deque.peekLast()] <= nums[i]) deque.removeLast();
            deque.addLast(i);
            if (i >= k - 1) answer[out++] = nums[deque.peekFirst()];
        }
        return answer;
    }

    static int[] oracle(int[] nums, int k) {
        int[] answer = new int[nums.length - k + 1];
        for (int left = 0; left + k <= nums.length; left++) {
            int max = nums[left];
            for (int j = left + 1; j < left + k; j++) max = Math.max(max, nums[j]);
            answer[left] = max;
        }
        return answer;
    }

    static void check(int[] nums, int k) {
        int[] actual = solve(nums, k), expected = oracle(nums, k);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError("nums=" + Arrays.toString(nums) + " k=" + k + " actual=" + Arrays.toString(actual) + " expected=" + Arrays.toString(expected));
        }
    }

    public static void main(String[] args) {
        check(new int[]{1,3,-1,-3,5,3,6,7}, 3);
        check(new int[]{1}, 1);
        check(new int[]{4,3,2,1}, 2);
        check(new int[]{1,2,3,4}, 2);
        check(new int[]{2,2,2,2}, 2);
        check(new int[]{-4,-2,-5,-1}, 2);
        check(new int[]{9,1,9,1,9}, 3);
        check(new int[]{5,1,4,3,2}, 5);
        if (!Arrays.equals(solve(new int[]{7,6,5},1), new int[]{7,6,5})) throw new AssertionError("k=1 boundary failed");
        try { solve(new int[]{1,2},0); throw new AssertionError("k=0 accepted"); } catch (IllegalArgumentException expected) {}
        try { solve(new int[]{1,2},3); throw new AssertionError("k>n accepted"); } catch (IllegalArgumentException expected) {}
        try { solve(null,1); throw new AssertionError("null accepted"); } catch (IllegalArgumentException expected) {}
        Random random = new Random(20260826L);
        for (int t = 0; t < 5000; t++) {
            int n = 1 + random.nextInt(40);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) nums[i] = random.nextInt(41) - 20;
            int k = 1 + random.nextInt(n);
            check(nums, k);
        }
        System.out.println("PASS fixed=9 boundaries=3 randomized=5000 oracle=quadratic-window-scan");
    }
}
