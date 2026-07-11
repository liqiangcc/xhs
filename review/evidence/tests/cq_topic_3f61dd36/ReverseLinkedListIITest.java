public final class ReverseLinkedListIITest {
    private ReverseLinkedListIITest() {}

    private static ReverseLinkedListII.ListNode list(int... values) {
        ReverseLinkedListII.ListNode dummy = new ReverseLinkedListII.ListNode(0);
        ReverseLinkedListII.ListNode tail = dummy;
        for (int value : values) { tail.next = new ReverseLinkedListII.ListNode(value); tail = tail.next; }
        return dummy.next;
    }

    private static String text(ReverseLinkedListII.ListNode head) {
        StringBuilder out = new StringBuilder();
        for (ReverseLinkedListII.ListNode node = head; node != null; node = node.next) {
            if (out.length() > 0) out.append(',');
            out.append(node.value);
        }
        return out.toString();
    }

    private static void require(String actual, String expected) {
        if (!actual.equals(expected)) throw new AssertionError("expected " + expected + " but was " + actual);
    }

    public static void main(String[] args) {
        require(text(ReverseLinkedListII.reverseBetween(list(1, 2, 3, 4, 5), 2, 4)), "1,4,3,2,5");
        require(text(ReverseLinkedListII.reverseBetween(list(1, 2, 3), 1, 2)), "2,1,3");
        require(text(ReverseLinkedListII.reverseBetween(list(1, 2, 3), 2, 2)), "1,2,3");
        require(text(ReverseLinkedListII.reverseBetween(list(1, 2, 3), 1, 3)), "3,2,1");
        if (ReverseLinkedListII.reverseBetween(null, 1, 1) != null) throw new AssertionError("null must remain null");
    }
}
