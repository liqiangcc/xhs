public final class ReverseKGroup {
    private ReverseKGroup() {}

    public static final class ListNode {
        public final int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }

    public static ListNode reverseKGroup(ListNode head, int k) {
        if (k < 1) throw new IllegalArgumentException("k must be >= 1");
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode groupPrev = dummy;
        while (true) {
            ListNode kth = kthFrom(groupPrev, k);
            if (kth == null) break;
            ListNode groupNext = kth.next;
            ListNode prev = groupNext;
            ListNode cur = groupPrev.next;
            while (cur != groupNext) {
                ListNode next = cur.next;
                cur.next = prev;
                prev = cur;
                cur = next;
            }
            ListNode oldGroupHead = groupPrev.next;
            groupPrev.next = kth;
            groupPrev = oldGroupHead;
        }
        return dummy.next;
    }

    private static ListNode kthFrom(ListNode start, int k) {
        ListNode cur = start;
        for (int i = 0; i < k; i++) {
            cur = cur.next;
            if (cur == null) return null;
        }
        return cur;
    }
}
