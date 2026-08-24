public final class RemoveAllDuplicates {
    public static final class ListNode {
        final int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    public static ListNode deleteDuplicates(ListNode head) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy;
        ListNode cur = head;
        while (cur != null) {
            if (cur.next != null && cur.val == cur.next.val) {
                int duplicateValue = cur.val;
                while (cur != null && cur.val == duplicateValue) {
                    cur = cur.next;
                }
                prev.next = cur;
            } else {
                prev = cur;
                cur = cur.next;
            }
        }
        return dummy.next;
    }

    private RemoveAllDuplicates() {}
}
