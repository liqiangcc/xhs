public final class DeleteAllDuplicateValues {
    public static final class ListNode {
        public int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }

    public static ListNode deleteAllDuplicates(ListNode head) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy;
        ListNode current = head;

        while (current != null) {
            boolean duplicated = false;
            ListNode runnerPrev = current;
            ListNode runner = current.next;
            while (runner != null) {
                if (runner.val == current.val) {
                    duplicated = true;
                    runnerPrev.next = runner.next;
                    runner = runnerPrev.next;
                } else {
                    runnerPrev = runner;
                    runner = runner.next;
                }
            }

            if (duplicated) {
                prev.next = current.next;
                current = prev.next;
            } else {
                prev = current;
                current = current.next;
            }
        }
        return dummy.next;
    }
}
