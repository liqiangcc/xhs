public final class SwapNodesInPairs {
    private SwapNodesInPairs() {}

    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static ListNode swapPairs(ListNode head) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy;
        while (prev.next != null && prev.next.next != null) {
            ListNode first = prev.next;
            ListNode second = first.next;
            ListNode rest = second.next;
            first.next = rest;
            second.next = first;
            prev.next = second;
            prev = first;
        }
        return dummy.next;
    }
}
