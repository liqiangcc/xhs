public final class LinkedListIntersection {
    private LinkedListIntersection() {}
    public static final class Node {
        public final int value;
        public Node next;
        public Node(int value) { this.value = value; }
    }
    public static Node firstCommon(Node headA, Node headB) {
        Node a = headA, b = headB;
        while (a != b) {
            a = (a == null) ? headB : a.next;
            b = (b == null) ? headA : b.next;
        }
        return a;
    }
}
