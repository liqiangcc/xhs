import java.util.Objects;

public final class ReverseBetween {
    public static final class ListNode {
        public final int value;
        public ListNode next;

        public ListNode(int value) {
            this(value, null);
        }

        public ListNode(int value, ListNode next) {
            this.value = value;
            this.next = next;
        }
    }

    private ReverseBetween() {}

    /**
     * Reverses the inclusive 1-based range [m, n] in one forward traversal.
     * Contract for this candidate: head is non-null and 1 <= m <= n <= list length.
     */
    public static ListNode reverseBetween(ListNode head, int m, int n) {
        Objects.requireNonNull(head, "head");
        if (m < 1 || n < m) {
            throw new IllegalArgumentException("expected 1 <= m <= n");
        }

        ListNode dummy = new ListNode(0, head);
        ListNode before = dummy;
        for (int position = 1; position < m; position++) {
            before = before.next;
        }

        ListNode current = before.next;
        for (int moved = 0; moved < n - m; moved++) {
            ListNode moving = current.next;
            current.next = moving.next;
            moving.next = before.next;
            before.next = moving;
        }
        return dummy.next;
    }
}
