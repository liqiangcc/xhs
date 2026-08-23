import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class BinaryTreeSubstructureTest {
    private static int fixedChecks = 0;

    public static void main(String[] args) {
        check(null, null, false);
        check(n(1), null, false);
        check(null, n(1), false);
        check(n(1), n(1), true);

        BinaryTreeSubstructure.Node a1 = n(3);
        a1.left = n(4); a1.right = n(5);
        a1.left.left = n(1); a1.left.right = n(2);
        BinaryTreeSubstructure.Node b1 = n(4);
        b1.left = n(1);
        check(a1, b1, true);

        BinaryTreeSubstructure.Node b2 = n(4);
        b2.left = n(1); b2.right = n(3);
        check(a1, b2, false);

        BinaryTreeSubstructure.Node repeated = n(1);
        repeated.left = n(1); repeated.right = n(1);
        repeated.left.left = n(2);
        BinaryTreeSubstructure.Node target = n(1);
        target.left = n(2);
        check(repeated, target, true);

        BinaryTreeSubstructure.Node rootOnly = n(-2);
        rootOnly.left = n(8);
        check(rootOnly, n(-2), true);

        BinaryTreeSubstructure.Node extraA = n(7);
        extraA.left = n(3); extraA.right = n(9);
        extraA.left.left = n(1); extraA.left.right = n(5);
        BinaryTreeSubstructure.Node partialB = n(3);
        partialB.right = n(5);
        check(extraA, partialB, true);

        Random random = new Random(0x2c267f2fL);
        int randomized = 5000;
        for (int i = 0; i < randomized; i++) {
            BinaryTreeSubstructure.Node a = randomTree(random, random.nextInt(36));
            BinaryTreeSubstructure.Node b = randomTree(random, random.nextInt(9));
            String beforeA = serialize(a);
            String beforeB = serialize(b);
            boolean expected = oracle(a, b);
            boolean actual = BinaryTreeSubstructure.isSubstructure(a, b);
            if (actual != expected) {
                throw new AssertionError("random mismatch iteration=" + i
                        + " expected=" + expected + " actual=" + actual
                        + " A=" + beforeA + " B=" + beforeB);
            }
            if (!beforeA.equals(serialize(a)) || !beforeB.equals(serialize(b))) {
                throw new AssertionError("tree mutated at iteration=" + i);
            }
        }

        System.out.println("PASS fixed=" + fixedChecks
                + " randomized=" + randomized
                + " oracle=enumerate-roots-and-match emptyB=false mutation=none");
    }

    private static BinaryTreeSubstructure.Node n(int value) {
        return new BinaryTreeSubstructure.Node(value);
    }

    private static void check(BinaryTreeSubstructure.Node a, BinaryTreeSubstructure.Node b, boolean expected) {
        fixedChecks++;
        String beforeA = serialize(a);
        String beforeB = serialize(b);
        boolean actual = BinaryTreeSubstructure.isSubstructure(a, b);
        if (actual != expected) {
            throw new AssertionError("fixed mismatch expected=" + expected + " actual=" + actual);
        }
        if (actual != oracle(a, b)) {
            throw new AssertionError("fixed oracle mismatch");
        }
        if (!beforeA.equals(serialize(a)) || !beforeB.equals(serialize(b))) {
            throw new AssertionError("fixed tree mutated");
        }
    }

    private static boolean oracle(BinaryTreeSubstructure.Node a, BinaryTreeSubstructure.Node b) {
        if (a == null || b == null) {
            return false;
        }
        List<BinaryTreeSubstructure.Node> roots = new ArrayList<>();
        collect(a, roots);
        for (BinaryTreeSubstructure.Node root : roots) {
            if (bruteMatch(root, b)) {
                return true;
            }
        }
        return false;
    }

    private static void collect(BinaryTreeSubstructure.Node node, List<BinaryTreeSubstructure.Node> out) {
        if (node == null) return;
        out.add(node);
        collect(node.left, out);
        collect(node.right, out);
    }

    private static boolean bruteMatch(BinaryTreeSubstructure.Node a, BinaryTreeSubstructure.Node b) {
        if (b == null) return true;
        if (a == null || a.value != b.value) return false;
        return bruteMatch(a.left, b.left) && bruteMatch(a.right, b.right);
    }

    private static BinaryTreeSubstructure.Node randomTree(Random random, int size) {
        if (size == 0) return null;
        BinaryTreeSubstructure.Node root = n(random.nextInt(9) - 4);
        List<BinaryTreeSubstructure.Node> open = new ArrayList<>();
        open.add(root);
        int created = 1;
        while (created < size) {
            int parentIndex = random.nextInt(open.size());
            BinaryTreeSubstructure.Node parent = open.get(parentIndex);
            if (parent.left != null && parent.right != null) {
                open.remove(parentIndex);
                continue;
            }
            BinaryTreeSubstructure.Node child = n(random.nextInt(9) - 4);
            if (parent.left == null && (parent.right != null || random.nextBoolean())) {
                parent.left = child;
            } else {
                parent.right = child;
            }
            if (parent.left != null && parent.right != null) open.remove(parentIndex);
            open.add(child);
            created++;
        }
        return root;
    }

    private static String serialize(BinaryTreeSubstructure.Node node) {
        StringBuilder out = new StringBuilder();
        serialize(node, out);
        return out.toString();
    }

    private static void serialize(BinaryTreeSubstructure.Node node, StringBuilder out) {
        if (node == null) { out.append('#'); return; }
        out.append('(').append(node.value).append(' ');
        serialize(node.left, out);
        out.append(' ');
        serialize(node.right, out);
        out.append(')');
    }
}
