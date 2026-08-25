public final class LinkedListIntersection {
    public static final class Node {
        public final int value;
        public Node next;
        public Node(int value) { this.value = value; }
    }

    public static Node firstIntersection(Node headA, Node headB) {
        Node p = headA;
        Node q = headB;
        while (p != q) {
            p = (p == null) ? headB : p.next;
            q = (q == null) ? headA : q.next;
        }
        return p;
    }
}
