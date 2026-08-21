import java.util.HashSet;
import java.util.Set;

public final class LinkedListFirstCommonNode {
    public static final class Node {
        public final int value;
        public Node next;

        public Node(int value) {
            this.value = value;
        }
    }

    public static Node firstBySwitching(Node headA, Node headB) {
        Node p = headA;
        Node q = headB;
        while (p != q) {
            p = (p == null) ? headB : p.next;
            q = (q == null) ? headA : q.next;
        }
        return p;
    }

    public static Node firstByHash(Node headA, Node headB) {
        Set<Node> seen = new HashSet<>();
        for (Node p = headA; p != null; p = p.next) {
            seen.add(p);
        }
        for (Node q = headB; q != null; q = q.next) {
            if (seen.contains(q)) {
                return q;
            }
        }
        return null;
    }

    public static Node firstByAlignedLength(Node headA, Node headB) {
        int lenA = length(headA);
        int lenB = length(headB);
        Node p = headA;
        Node q = headB;

        for (int i = lenA - lenB; i > 0; i--) {
            p = p.next;
        }
        for (int i = lenB - lenA; i > 0; i--) {
            q = q.next;
        }

        while (p != q) {
            p = p.next;
            q = q.next;
        }
        return p;
    }

    private static int length(Node head) {
        int length = 0;
        for (Node p = head; p != null; p = p.next) {
            length++;
        }
        return length;
    }
}
