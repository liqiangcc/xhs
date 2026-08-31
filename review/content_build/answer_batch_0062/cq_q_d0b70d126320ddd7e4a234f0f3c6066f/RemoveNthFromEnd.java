public final class RemoveNthFromEnd {
    public static final class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    public static ListNode removeNthFromEnd(ListNode head, int n) {
        if (n <= 0) throw new IllegalArgumentException("n must be positive");
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode fast = dummy, slow = dummy;
        for (int i = 0; i < n; i++) {
            fast = fast.next;
            if (fast == null) throw new IllegalArgumentException("n exceeds list length");
        }
        while (fast.next != null) {
            fast = fast.next;
            slow = slow.next;
        }
        slow.next = slow.next.next;
        return dummy.next;
    }
}
