import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Objects;

public final class LinkedListBigIntegerAdd {
    private LinkedListBigIntegerAdd() {}

    public static final class ListNode {
        public final int digit;
        public ListNode next;

        public ListNode(int digit) {
            this(digit, null);
        }

        public ListNode(int digit, ListNode next) {
            if (digit < 0 || digit > 9) {
                throw new IllegalArgumentException("digit must be in [0, 9]");
            }
            this.digit = digit;
            this.next = next;
        }
    }

    public static ListNode add(ListNode left, ListNode right) {
        Objects.requireNonNull(left, "left");
        Objects.requireNonNull(right, "right");

        Deque<Integer> leftDigits = digits(left);
        Deque<Integer> rightDigits = digits(right);
        ListNode result = null;
        int carry = 0;

        while (!leftDigits.isEmpty() || !rightDigits.isEmpty() || carry != 0) {
            int sum = carry;
            if (!leftDigits.isEmpty()) sum += leftDigits.pop();
            if (!rightDigits.isEmpty()) sum += rightDigits.pop();
            result = new ListNode(sum % 10, result);
            carry = sum / 10;
        }
        return result;
    }

    private static Deque<Integer> digits(ListNode head) {
        Deque<Integer> stack = new ArrayDeque<>();
        for (ListNode node = head; node != null; node = node.next) {
            stack.push(node.digit);
        }
        return stack;
    }
}
