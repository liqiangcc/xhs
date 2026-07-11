public final class ReverseLinkedListTest {
    private static ReverseLinkedList.ListNode list(int... values) {
        ReverseLinkedList.ListNode dummy = new ReverseLinkedList.ListNode(0), tail = dummy;
        for (int value : values) { tail.next = new ReverseLinkedList.ListNode(value); tail = tail.next; }
        return dummy.next;
    }
    private static String text(ReverseLinkedList.ListNode node) {
        StringBuilder out = new StringBuilder();
        while (node != null) { if (out.length() > 0) out.append(','); out.append(node.value); node = node.next; }
        return out.toString();
    }
    private static void require(String actual, String expected) { if (!actual.equals(expected)) throw new AssertionError(actual); }
    public static void main(String[] args) {
        if (ReverseLinkedList.reverse(null) != null) throw new AssertionError("null");
        require(text(ReverseLinkedList.reverse(list(7))), "7");
        require(text(ReverseLinkedList.reverse(list(1, 2))), "2,1");
        ReverseLinkedList.ListNode originalHead = list(1, 2, 3, 4);
        require(text(ReverseLinkedList.reverse(originalHead)), "4,3,2,1");
        if (originalHead.next != null) throw new AssertionError("original head must become tail");
    }
}
