import java.util.*;

public final class LeetCode1769 {
    public static int[] minOperations(String boxes) {
        int n = boxes.length();
        int[] answer = new int[n];
        int balls = 0;
        int moves = 0;
        for (int i = 0; i < n; i++) {
            answer[i] += moves;
            if (boxes.charAt(i) == '1') balls++;
            moves += balls;
        }
        balls = 0;
        moves = 0;
        for (int i = n - 1; i >= 0; i--) {
            answer[i] += moves;
            if (boxes.charAt(i) == '1') balls++;
            moves += balls;
        }
        return answer;
    }

    static int[] brute(String boxes) {
        int n = boxes.length();
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (boxes.charAt(j) == '1') out[i] += Math.abs(i - j);
            }
        }
        return out;
    }

    static void check(String boxes, int[] expected) {
        int[] actual = minOperations(boxes);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError(boxes + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        }
        if (!Arrays.equals(actual, brute(boxes))) {
            throw new AssertionError(boxes + " disagrees with brute force");
        }
    }

    public static void main(String[] args) {
        check("0", new int[]{0});
        check("1", new int[]{0});
        check("110", new int[]{1, 1, 3});
        check("001011", new int[]{11, 8, 5, 4, 3, 4});
        check("111", new int[]{3, 2, 3});
        for (int n = 1; n <= 8; n++) {
            for (int mask = 0; mask < (1 << n); mask++) {
                StringBuilder b = new StringBuilder(n);
                for (int i = 0; i < n; i++) b.append(((mask >>> i) & 1) == 1 ? '1' : '0');
                String boxes = b.toString();
                int[] actual = minOperations(boxes);
                int[] brute = brute(boxes);
                if (!Arrays.equals(actual, brute)) throw new AssertionError("exhaustive mismatch " + boxes);
            }
        }
        System.out.println("PASS examples=2 singletons=2 all-balls=1 exhaustive-binary-strings-length<=8");
    }
}
