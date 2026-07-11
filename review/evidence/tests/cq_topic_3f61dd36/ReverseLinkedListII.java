public final class ReverseLinkedListII {
    private ReverseLinkedListII() {}

    public static final class ListNode {
        public final int value;
        public ListNode next;

        public ListNode(int value) {
            this.value = value;
        }
    }

    public static ListNode reverseBetween(ListNode head, int left, int right) {
        if (head == null) {
            return null;
        }
        if (left < 1 || right < left) {
            throw new IllegalArgumentException("invalid range");
        }
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode pre = dummy;
        for (int position = 1; position < left; position++) {
            if (pre.next == null) {
                throw new IllegalArgumentException("left exceeds list length");
            }
            pre = pre.next;
        }
        ListNode segmentHead = pre.next;
        if (segmentHead == null) {
            throw new IllegalArgumentException("left exceeds list length");
        }
        for (int moved = 0; moved < right - left; moved++) {
            ListNode moving = segmentHead.next;
            if (moving == null) {
                throw new IllegalArgumentException("right exceeds list length");
            }
            segmentHead.next = moving.next;
            moving.next = pre.next;
            pre.next = moving;
        }
        return dummy.next;
    }
}
