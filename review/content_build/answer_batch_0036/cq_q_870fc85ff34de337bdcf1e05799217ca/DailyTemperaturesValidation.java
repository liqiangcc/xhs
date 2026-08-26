import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
import java.util.Random;

public final class DailyTemperaturesValidation {
    static int[] solve(int[] temperatures) {
        int n = temperatures.length;
        int[] answer = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();
        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && temperatures[i] > temperatures[stack.peek()]) {
                int j = stack.pop();
                answer[j] = i - j;
            }
            stack.push(i);
        }
        return answer;
    }

    static int[] oracle(int[] temperatures) {
        int[] answer = new int[temperatures.length];
        for (int i = 0; i < temperatures.length; i++) {
            for (int j = i + 1; j < temperatures.length; j++) {
                if (temperatures[j] > temperatures[i]) {
                    answer[i] = j - i;
                    break;
                }
            }
        }
        return answer;
    }

    static void check(int[] input, int[] expected) {
        int[] actual = solve(input);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError("input=" + Arrays.toString(input)
                    + " expected=" + Arrays.toString(expected)
                    + " actual=" + Arrays.toString(actual));
        }
    }

    public static void main(String[] args) {
        check(new int[]{}, new int[]{});
        check(new int[]{70}, new int[]{0});
        check(new int[]{73,74,75,71,69,72,76,73}, new int[]{1,1,4,2,1,1,0,0});
        check(new int[]{30,40,50,60}, new int[]{1,1,1,0});
        check(new int[]{60,50,40,30}, new int[]{0,0,0,0});
        check(new int[]{70,70,71}, new int[]{2,1,0});
        check(new int[]{71,70,70,72}, new int[]{3,2,1,0});
        check(new int[]{70,71,70,71,72}, new int[]{1,3,1,1,0});

        Random random = new Random(20260826L);
        int randomized = 5000;
        long checkedElements = 0;
        for (int round = 0; round < randomized; round++) {
            int n = random.nextInt(80);
            int[] input = new int[n];
            for (int i = 0; i < n; i++) input[i] = 20 + random.nextInt(81);
            int[] expected = oracle(input);
            int[] actual = solve(input);
            if (!Arrays.equals(actual, expected)) {
                throw new AssertionError("round=" + round
                        + " input=" + Arrays.toString(input)
                        + " expected=" + Arrays.toString(expected)
                        + " actual=" + Arrays.toString(actual));
            }
            checkedElements += n;
        }
        System.out.println("PASS fixed=8 randomized=5000 oracle=quadratic-next-warmer strict-greater=true duplicates=true empty=true single=true checked-elements=" + checkedElements);
    }
}
