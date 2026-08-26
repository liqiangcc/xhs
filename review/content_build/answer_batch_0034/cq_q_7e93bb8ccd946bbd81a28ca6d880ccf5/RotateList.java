public final class RotateList {
    public static final class ListNode {
        public int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }

    public static ListNode rotateRight(ListNode head, int k) {
        if (k < 0) throw new IllegalArgumentException("k must be non-negative");
        if (head == null || head.next == null || k == 0) return head;

        int n = 1;
        ListNode tail = head;
        while (tail.next != null) {
            tail = tail.next;
            n++;
        }

        int shift = k % n;
        if (shift == 0) return head;

        tail.next = head;
        int stepsToNewTail = n - shift - 1;
        ListNode newTail = head;
        for (int i = 0; i < stepsToNewTail; i++) {
            newTail = newTail.next;
        }

        ListNode newHead = newTail.next;
        newTail.next = null;
        return newHead;
    }
}
