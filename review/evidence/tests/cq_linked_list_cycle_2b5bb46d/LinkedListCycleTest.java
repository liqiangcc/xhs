public final class LinkedListCycleTest {
    private static void require(boolean actual, boolean expected, String name) {
        if (actual != expected) throw new AssertionError(name + ": expected " + expected + ", got " + actual);
    }

    private static boolean referenceHasCycle(LinkedListCycle.ListNode head) {
        boolean[] seen = new boolean[4];
        LinkedListCycle.ListNode current = head;
        while (current != null) {
            if (seen[current.value]) return true;
            seen[current.value] = true;
            current = current.next;
        }
        return false;
    }

    private static void exhaustiveFourNodeFunctionalGraphs() {
        for (int encoding = 0; encoding < 625; encoding++) {
            LinkedListCycle.ListNode[] nodes = new LinkedListCycle.ListNode[4];
            for (int i = 0; i < nodes.length; i++) nodes[i] = new LinkedListCycle.ListNode(i);
            int value = encoding;
            for (int i = 0; i < nodes.length; i++) {
                int next = value % 5;
                value /= 5;
                nodes[i].next = next == 4 ? null : nodes[next];
            }
            require(LinkedListCycle.hasCycle(nodes[0]), referenceHasCycle(nodes[0]), "exhaustive " + encoding);
        }
    }

    public static void main(String[] args) {
        require(LinkedListCycle.hasCycle(null), false, "null");
        LinkedListCycle.ListNode one = new LinkedListCycle.ListNode(0);
        require(LinkedListCycle.hasCycle(one), false, "one-node no cycle");
        one.next = one;
        require(LinkedListCycle.hasCycle(one), true, "self loop");
        LinkedListCycle.ListNode first = new LinkedListCycle.ListNode(0);
        LinkedListCycle.ListNode second = new LinkedListCycle.ListNode(1);
        first.next = second; second.next = first;
        require(LinkedListCycle.hasCycle(first), true, "two-node cycle");
        exhaustiveFourNodeFunctionalGraphs();
    }
}
