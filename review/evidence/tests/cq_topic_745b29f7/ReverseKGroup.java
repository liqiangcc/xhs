public final class ReverseKGroup {
    private ReverseKGroup() {}
    public static final class ListNode {
        public final int value; public ListNode next;
        public ListNode(int value) { this.value = value; }
    }
    public static ListNode reverseKGroup(ListNode head, int k) {
        if (k < 1) throw new IllegalArgumentException("k must be positive");
        ListNode dummy = new ListNode(0); dummy.next = head;
        ListNode groupPrev = dummy;
        while (true) {
            ListNode kth = groupPrev;
            for (int step = 0; step < k && kth != null; step++) kth = kth.next;
            if (kth == null) return dummy.next;
            ListNode groupNext = kth.next;
            ListNode previous = groupNext;
            ListNode current = groupPrev.next;
            while (current != groupNext) {
                ListNode next = current.next; current.next = previous; previous = current; current = next;
            }
            ListNode oldHead = groupPrev.next;
            groupPrev.next = kth;
            groupPrev = oldHead;
        }
    }
}
