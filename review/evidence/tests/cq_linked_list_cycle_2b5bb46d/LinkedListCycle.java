public final class LinkedListCycle {
    private LinkedListCycle() {}
    public static final class ListNode {
        public final int value; public ListNode next;
        public ListNode(int value) { this.value = value; }
    }
    public static boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }
}
