public final class LinkedListIntersectionWriterTest {
    private static long intersectingCases = 0;
    private static long disjointCases = 0;

    public static void main(String[] args) {
        if (LinkedListIntersection.firstCommon(null, null) != null) throw new AssertionError("empty");
        LinkedListIntersection.Node same = chain(3, 9000, null);
        if (LinkedListIntersection.firstCommon(same, same) != same) throw new AssertionError("same head");
        for (int a = 0; a <= 30; a++) {
            for (int b = 0; b <= 30; b++) {
                for (int c = 1; c <= 20; c++) {
                    LinkedListIntersection.Node shared = chain(c, 100000, null);
                    LinkedListIntersection.Node ha = chain(a, 1000, shared);
                    LinkedListIntersection.Node hb = chain(b, 2000, shared);
                    if (LinkedListIntersection.firstCommon(ha, hb) != shared) throw new AssertionError("wrong intersection a="+a+" b="+b+" c="+c);
                    intersectingCases++;
                }
                LinkedListIntersection.Node ha = chain(a, 3000, null);
                LinkedListIntersection.Node hb = chain(b, 4000, null);
                if (LinkedListIntersection.firstCommon(ha, hb) != null) throw new AssertionError("false intersection");
                disjointCases++;
            }
        }
        LinkedListIntersection.Node v1 = new LinkedListIntersection.Node(7);
        LinkedListIntersection.Node v2 = new LinkedListIntersection.Node(7);
        if (LinkedListIntersection.firstCommon(v1, v2) != null) throw new AssertionError("equal values are not shared nodes");
        System.out.printf("PASS intersecting_cases=%d disjoint_cases=%d same_head=pass equal_value_distinct=pass empty=pass%n", intersectingCases, disjointCases);
    }

    private static LinkedListIntersection.Node chain(int n, int base, LinkedListIntersection.Node tail) {
        LinkedListIntersection.Node head = tail;
        for (int i = n - 1; i >= 0; i--) {
            LinkedListIntersection.Node x = new LinkedListIntersection.Node(base + i);
            x.next = head;
            head = x;
        }
        return head;
    }
}
