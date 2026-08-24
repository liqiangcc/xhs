import java.util.Random;

public final class LinkedListFirstCommonNodeTest {
    private static final long SEED = 0x5EED08084CL;

    public static void main(String[] args) {
        testBothNull();
        testOneNull();
        testSameHead();
        testSharedTailOnly();
        testUnequalPrefixes();
        testEqualValuesButDifferentNodes();
        randomizedStructures();
        System.out.println("PASS fixed=6 randomized=3000 methods=3 identity=verified");
    }

    private static void testBothNull() {
        assertAll(null, null, null, "both-null");
    }

    private static void testOneNull() {
        LinkedListFirstCommonNode.Node a = chain(1, 2, 3);
        assertAll(a, null, null, "one-null-a");
        assertAll(null, a, null, "one-null-b");
    }

    private static void testSameHead() {
        LinkedListFirstCommonNode.Node shared = chain(7, 8, 9);
        assertAll(shared, shared, shared, "same-head");
    }

    private static void testSharedTailOnly() {
        LinkedListFirstCommonNode.Node shared = new LinkedListFirstCommonNode.Node(99);
        LinkedListFirstCommonNode.Node a = append(chain(1, 2), shared);
        LinkedListFirstCommonNode.Node b = append(chain(3, 4, 5), shared);
        assertAll(a, b, shared, "shared-tail-node");
    }

    private static void testUnequalPrefixes() {
        LinkedListFirstCommonNode.Node shared = chain(50, 51, 52);
        LinkedListFirstCommonNode.Node a = append(chain(1, 2, 3, 4), shared);
        LinkedListFirstCommonNode.Node b = append(chain(10), shared);
        assertAll(a, b, shared, "unequal-prefixes");
    }

    private static void testEqualValuesButDifferentNodes() {
        LinkedListFirstCommonNode.Node a = chain(1, 2, 3);
        LinkedListFirstCommonNode.Node b = chain(1, 2, 3);
        assertAll(a, b, null, "equal-values-disjoint-identities");
    }

    private static void randomizedStructures() {
        Random random = new Random(SEED);
        for (int round = 0; round < 3000; round++) {
            int prefixA = random.nextInt(18);
            int prefixB = random.nextInt(18);
            int sharedLength = random.nextInt(10);

            LinkedListFirstCommonNode.Node shared = sharedLength == 0
                ? null
                : chainWithLength(100000 + round * 20, sharedLength);
            LinkedListFirstCommonNode.Node aPrefix = chainWithLength(round * 100, prefixA);
            LinkedListFirstCommonNode.Node bPrefix = chainWithLength(round * 100 + 50, prefixB);
            LinkedListFirstCommonNode.Node a = append(aPrefix, shared);
            LinkedListFirstCommonNode.Node b = append(bPrefix, shared);
            assertAll(a, b, shared, "random-" + round);
        }
    }

    private static void assertAll(
        LinkedListFirstCommonNode.Node a,
        LinkedListFirstCommonNode.Node b,
        LinkedListFirstCommonNode.Node expected,
        String label
    ) {
        assertSame(expected, LinkedListFirstCommonNode.firstBySwitching(a, b), label + "-switching");
        assertSame(expected, LinkedListFirstCommonNode.firstByHash(a, b), label + "-hash");
        assertSame(expected, LinkedListFirstCommonNode.firstByAlignedLength(a, b), label + "-aligned");
    }

    private static LinkedListFirstCommonNode.Node chain(int... values) {
        LinkedListFirstCommonNode.Node head = null;
        LinkedListFirstCommonNode.Node tail = null;
        for (int value : values) {
            LinkedListFirstCommonNode.Node node = new LinkedListFirstCommonNode.Node(value);
            if (head == null) {
                head = node;
            } else {
                tail.next = node;
            }
            tail = node;
        }
        return head;
    }

    private static LinkedListFirstCommonNode.Node chainWithLength(int start, int length) {
        LinkedListFirstCommonNode.Node head = null;
        LinkedListFirstCommonNode.Node tail = null;
        for (int i = 0; i < length; i++) {
            LinkedListFirstCommonNode.Node node = new LinkedListFirstCommonNode.Node(start + i);
            if (head == null) {
                head = node;
            } else {
                tail.next = node;
            }
            tail = node;
        }
        return head;
    }

    private static LinkedListFirstCommonNode.Node append(
        LinkedListFirstCommonNode.Node prefix,
        LinkedListFirstCommonNode.Node suffix
    ) {
        if (prefix == null) {
            return suffix;
        }
        LinkedListFirstCommonNode.Node tail = prefix;
        while (tail.next != null) {
            tail = tail.next;
        }
        tail.next = suffix;
        return prefix;
    }

    private static void assertSame(
        LinkedListFirstCommonNode.Node expected,
        LinkedListFirstCommonNode.Node actual,
        String label
    ) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected identity "
                + identity(expected) + ", actual " + identity(actual));
        }
    }

    private static String identity(LinkedListFirstCommonNode.Node node) {
        return node == null ? "null" : node.value + "@" + System.identityHashCode(node);
    }
}
