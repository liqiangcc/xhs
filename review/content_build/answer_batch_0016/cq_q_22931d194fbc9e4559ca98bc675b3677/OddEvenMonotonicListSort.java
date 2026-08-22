public final class OddEvenMonotonicListSort {
    private OddEvenMonotonicListSort() {}

    public static final class Node {
        public final int value;
        public Node next;

        public Node(int value) {
            this.value = value;
        }
    }

    /**
     * Sorts in place a list whose odd-position values are nondecreasing and
     * whose even-position values are nonincreasing. Returns the new head.
     */
    public static Node sort(Node head) {
        if (head == null || head.next == null) {
            return head;
        }

        Node oddHead = null;
        Node oddTail = null;
        Node evenHead = null;
        Node evenTail = null;

        Node current = head;
        boolean oddPosition = true;
        while (current != null) {
            Node next = current.next;
            current.next = null;
            if (oddPosition) {
                if (oddHead == null) {
                    oddHead = current;
                } else {
                    oddTail.next = current;
                }
                oddTail = current;
            } else {
                if (evenHead == null) {
                    evenHead = current;
                } else {
                    evenTail.next = current;
                }
                evenTail = current;
            }
            oddPosition = !oddPosition;
            current = next;
        }

        Node evenAscending = reverse(evenHead);
        return mergeAscending(oddHead, evenAscending);
    }

    private static Node reverse(Node head) {
        Node previous = null;
        Node current = head;
        while (current != null) {
            Node next = current.next;
            current.next = previous;
            previous = current;
            current = next;
        }
        return previous;
    }

    private static Node mergeAscending(Node a, Node b) {
        if (a == null) return b;
        if (b == null) return a;

        Node head;
        if (a.value <= b.value) {
            head = a;
            a = a.next;
        } else {
            head = b;
            b = b.next;
        }
        Node tail = head;

        while (a != null && b != null) {
            if (a.value <= b.value) {
                tail.next = a;
                a = a.next;
            } else {
                tail.next = b;
                b = b.next;
            }
            tail = tail.next;
        }
        tail.next = (a != null) ? a : b;
        return head;
    }
}
