import java.util.Random;

public final class TreeEqualityTest {
    private static int fixed = 0;

    public static void main(String[] args) {
        fixedCases();
        randomizedCases();
        System.out.println("PASS fixed=" + fixed + " randomized=5000 oracle=bfs-paired-tree-equality mutation=none");
    }

    private static void fixedCases() {
        check(null, null, true); // 1
        check(new TreeEquality.Node(1), null, false); // 2
        check(new TreeEquality.Node(7), new TreeEquality.Node(7), true); // 3
        check(new TreeEquality.Node(7), new TreeEquality.Node(8), false); // 4

        TreeEquality.Node a = node(1, node(2, null, null), node(3, null, null));
        TreeEquality.Node b = node(1, node(2, null, null), node(3, null, null));
        check(a, b, true); // 5

        TreeEquality.Node c = node(1, node(2, null, null), null);
        TreeEquality.Node d = node(1, null, node(2, null, null));
        check(c, d, false); // 6

        TreeEquality.Node e = node(1, node(1, node(1, null, null), null), node(1, null, null));
        TreeEquality.Node f = node(1, node(1, null, node(1, null, null)), node(1, null, null));
        check(e, f, false); // 7

        TreeEquality.Node g = node(4, node(3, node(2, node(1, null, null), null), null), null);
        TreeEquality.Node h = deepCopy(g);
        check(g, h, true); // 8
    }

    private static void randomizedCases() {
        Random random = new Random(0x5A17E0A1L);
        for (int i = 0; i < 5000; i++) {
            TreeEquality.Node a = randomTree(random, 0, 8);
            TreeEquality.Node b;
            int mode = random.nextInt(4);
            if (mode == 0) {
                b = deepCopy(a);
            } else if (mode == 1) {
                b = randomTree(random, 0, 8);
            } else if (mode == 2) {
                b = copyWithRootValueChanged(a);
            } else {
                b = copyWithExtraLeftmostChild(a);
            }

            String beforeA = serialize(a);
            String beforeB = serialize(b);
            boolean expected = TreeEquality.bfsOracle(a, b);
            boolean actual = TreeEquality.sameTree(a, b);
            if (actual != expected) {
                throw new AssertionError("random mismatch at case " + i + " expected=" + expected + " actual=" + actual
                        + " a=" + beforeA + " b=" + beforeB);
            }
            if (!beforeA.equals(serialize(a)) || !beforeB.equals(serialize(b))) {
                throw new AssertionError("input mutation detected at case " + i);
            }
        }
    }

    private static void check(TreeEquality.Node a, TreeEquality.Node b, boolean expected) {
        fixed++;
        String beforeA = serialize(a);
        String beforeB = serialize(b);
        boolean oracle = TreeEquality.bfsOracle(a, b);
        boolean actual = TreeEquality.sameTree(a, b);
        if (oracle != expected || actual != expected) {
            throw new AssertionError("fixed case " + fixed + " expected=" + expected + " oracle=" + oracle + " actual=" + actual);
        }
        if (!beforeA.equals(serialize(a)) || !beforeB.equals(serialize(b))) {
            throw new AssertionError("fixed case " + fixed + " mutated input");
        }
    }

    private static TreeEquality.Node randomTree(Random random, int depth, int maxDepth) {
        if (depth >= maxDepth || random.nextDouble() < (depth == 0 ? 0.12 : 0.28)) {
            return null;
        }
        TreeEquality.Node node = new TreeEquality.Node(random.nextInt(7) - 3);
        node.left = randomTree(random, depth + 1, maxDepth);
        node.right = randomTree(random, depth + 1, maxDepth);
        return node;
    }

    private static TreeEquality.Node deepCopy(TreeEquality.Node node) {
        if (node == null) return null;
        TreeEquality.Node copy = new TreeEquality.Node(node.value);
        copy.left = deepCopy(node.left);
        copy.right = deepCopy(node.right);
        return copy;
    }

    private static TreeEquality.Node copyWithRootValueChanged(TreeEquality.Node node) {
        if (node == null) {
            return new TreeEquality.Node(1000);
        }
        TreeEquality.Node copy = new TreeEquality.Node(node.value + 1000);
        copy.left = deepCopy(node.left);
        copy.right = deepCopy(node.right);
        return copy;
    }

    private static TreeEquality.Node copyWithExtraLeftmostChild(TreeEquality.Node node) {
        if (node == null) {
            return new TreeEquality.Node(999);
        }
        TreeEquality.Node copy = deepCopy(node);
        TreeEquality.Node cursor = copy;
        while (cursor.left != null) {
            cursor = cursor.left;
        }
        cursor.left = new TreeEquality.Node(999);
        return copy;
    }

    private static TreeEquality.Node node(int value, TreeEquality.Node left, TreeEquality.Node right) {
        TreeEquality.Node n = new TreeEquality.Node(value);
        n.left = left;
        n.right = right;
        return n;
    }

    private static String serialize(TreeEquality.Node node) {
        if (node == null) return "#";
        return node.value + "(" + serialize(node.left) + "," + serialize(node.right) + ")";
    }
}
