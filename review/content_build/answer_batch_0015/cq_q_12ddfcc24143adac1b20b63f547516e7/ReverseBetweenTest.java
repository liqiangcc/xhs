import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class ReverseBetweenTest {
    private static ReverseBetween.ListNode list(int... values) {
        ReverseBetween.ListNode dummy = new ReverseBetween.ListNode(0);
        ReverseBetween.ListNode tail = dummy;
        for (int value : values) {
            tail.next = new ReverseBetween.ListNode(value);
            tail = tail.next;
        }
        return dummy.next;
    }

    private static int[] values(ReverseBetween.ListNode head, int expectedLength) {
        int[] result = new int[expectedLength];
        ReverseBetween.ListNode node = head;
        for (int i = 0; i < expectedLength; i++) {
            if (node == null) throw new AssertionError("list ended early at index " + i);
            result[i] = node.value;
            node = node.next;
        }
        if (node != null) throw new AssertionError("list has extra nodes or a cycle");
        return result;
    }

    private static int[] oracle(int[] input, int m, int n) {
        int[] expected = Arrays.copyOf(input, input.length);
        for (int left = m - 1, right = n - 1; left < right; left++, right--) {
            int tmp = expected[left];
            expected[left] = expected[right];
            expected[right] = tmp;
        }
        return expected;
    }

    private static void assertCase(int[] input, int m, int n) {
        ReverseBetween.ListNode result = ReverseBetween.reverseBetween(list(input), m, n);
        int[] actual = values(result, input.length);
        int[] expected = oracle(input, m, n);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError(
                "input=" + Arrays.toString(input)
                    + " m=" + m
                    + " n=" + n
                    + " expected=" + Arrays.toString(expected)
                    + " actual=" + Arrays.toString(actual)
            );
        }
    }

    public static void main(String[] args) {
        List<int[]> fixedInputs = new ArrayList<>();
        fixedInputs.add(new int[]{1, 2, 3, 4, 5});
        fixedInputs.add(new int[]{1, 2, 3, 4, 5});
        fixedInputs.add(new int[]{1, 2, 3, 4, 5});
        fixedInputs.add(new int[]{1, 2, 3, 4, 5});
        fixedInputs.add(new int[]{1, 2, 3, 4, 5});
        fixedInputs.add(new int[]{7});
        fixedInputs.add(new int[]{8, 9});

        int[][] ranges = {
            {2, 4},
            {1, 3},
            {3, 5},
            {1, 5},
            {3, 3},
            {1, 1},
            {1, 2}
        };
        for (int i = 0; i < fixedInputs.size(); i++) {
            assertCase(fixedInputs.get(i), ranges[i][0], ranges[i][1]);
        }

        Random random = new Random(0x12ddfcc2L);
        int randomized = 5000;
        for (int round = 0; round < randomized; round++) {
            int length = 1 + random.nextInt(30);
            int[] input = new int[length];
            for (int i = 0; i < length; i++) input[i] = random.nextInt(2001) - 1000;
            int m = 1 + random.nextInt(length);
            int n = m + random.nextInt(length - m + 1);
            assertCase(input, m, n);
        }

        boolean nullRejected = false;
        try {
            ReverseBetween.reverseBetween(null, 1, 1);
        } catch (NullPointerException expected) {
            nullRejected = true;
        }
        if (!nullRejected) throw new AssertionError("null head must be rejected by candidate contract");

        boolean badRangeRejected = false;
        try {
            ReverseBetween.reverseBetween(list(1, 2, 3), 0, 2);
        } catch (IllegalArgumentException expected) {
            badRangeRejected = true;
        }
        if (!badRangeRejected) throw new AssertionError("m < 1 must be rejected");

        System.out.println("PASS fixed=7 randomized=" + randomized + " oracle=array-subrange-reversal ordered=true acyclic=true");
    }
}
