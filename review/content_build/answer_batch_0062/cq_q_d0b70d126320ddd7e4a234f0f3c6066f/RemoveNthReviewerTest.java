import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class RemoveNthReviewerTest {
    private static final Random RNG = new Random(0xD0B70D62L ^ 0x71A9E55L);

    static RemoveNthFromEnd.ListNode build(int[] values) {
        RemoveNthFromEnd.ListNode dummy = new RemoveNthFromEnd.ListNode(0), tail = dummy;
        for (int value : values) { tail.next = new RemoveNthFromEnd.ListNode(value); tail = tail.next; }
        return dummy.next;
    }

    static int[] values(RemoveNthFromEnd.ListNode head) {
        List<Integer> list = new ArrayList<>();
        for (RemoveNthFromEnd.ListNode p = head; p != null; p = p.next) list.add(p.val);
        int[] out = new int[list.size()];
        for (int i = 0; i < out.length; i++) out[i] = list.get(i);
        return out;
    }

    // Independent two-pass reference: first count length, then skip the 0-based target position.
    static int[] twoPassOracle(int[] input, int n) {
        int length = 0;
        for (int ignored : input) length++;
        int target = length - n;
        int[] out = new int[length - 1];
        int j = 0;
        for (int i = 0; i < length; i++) {
            if (i != target) out[j++] = input[i];
        }
        return out;
    }

    static void eq(int[] expected, int[] actual, String label) {
        if (!Arrays.equals(expected, actual)) {
            throw new AssertionError(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        }
    }

    static void fixed(int[] input, int n, int[] expected, String label) {
        eq(expected, values(RemoveNthFromEnd.removeNthFromEnd(build(input), n)), label);
    }

    public static void main(String[] args) {
        fixed(new int[]{1}, 1, new int[]{}, "single");
        fixed(new int[]{1,2}, 1, new int[]{1}, "tail-two");
        fixed(new int[]{1,2}, 2, new int[]{2}, "head-two");
        fixed(new int[]{1,2,3}, 2, new int[]{1,3}, "middle-three");
        fixed(new int[]{1,2,3,4,5}, 2, new int[]{1,2,3,5}, "example");
        fixed(new int[]{1,2,3,4,5}, 5, new int[]{2,3,4,5}, "head-five");
        fixed(new int[]{1,2,3,4,5}, 1, new int[]{1,2,3,4}, "tail-five");
        fixed(new int[]{7,7,7,7}, 3, new int[]{7,7,7}, "duplicates");
        fixed(new int[]{-3,-2,-1,0,1}, 4, new int[]{-3,-1,0,1}, "negative-values");
        fixed(new int[]{9,8,7,6}, 3, new int[]{9,7,6}, "middle-four");
        fixed(new int[]{42,5,42,5}, 4, new int[]{5,42,5}, "head-duplicate");
        fixed(new int[]{0,0,1,0,0}, 2, new int[]{0,0,1,0}, "zero-values");

        boolean bad0=false, badNeg=false, badLarge=false, badEmpty=false;
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1}), 0); } catch (IllegalArgumentException expected) { bad0=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1}), -7); } catch (IllegalArgumentException expected) { badNeg=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1,2}), 3); } catch (IllegalArgumentException expected) { badLarge=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(null, 1); } catch (IllegalArgumentException expected) { badEmpty=true; }
        if (!bad0 || !badNeg || !badLarge || !badEmpty) throw new AssertionError("declared invalid-input contract not enforced");

        int cases = 0;
        for (int t = 0; t < 40000; t++) {
            int len = 1 + RNG.nextInt(55);
            int n = 1 + RNG.nextInt(len);
            int[] input = new int[len];
            for (int i = 0; i < len; i++) input[i] = RNG.nextInt(31) - 15;
            int[] expected = twoPassOracle(input, n);
            int[] actual = values(RemoveNthFromEnd.removeNthFromEnd(build(input), n));
            eq(expected, actual, "random-" + t);
            cases++;
        }
        if (cases != 40000) throw new AssertionError("unexpected random case count " + cases);
        System.out.println("PASS reviewer fixed=12 random_cases=40000 oracle=two-pass-count invalid_n=pass head_delete=pass tail_delete=pass");
    }
}
