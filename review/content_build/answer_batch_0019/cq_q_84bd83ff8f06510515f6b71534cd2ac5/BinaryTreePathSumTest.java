import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Random;

public final class BinaryTreePathSumTest {
    private record State(BinaryTreePathSum.Node node, long sum) {}

    public static void main(String[] args) {
        int fixed = runFixed();
        int randomized = runRandomized(5000, 20260824L);
        System.out.println("PASS fixed=" + fixed + " randomized=" + randomized
                + " oracle=iterative-root-to-leaf-enumeration mutation=none");
    }

    private static int runFixed() {
        int count = 0;
        expect(false, BinaryTreePathSum.hasPathSum(null, 0), "null root"); count++;

        var single = new BinaryTreePathSum.Node(7);
        expect(true, BinaryTreePathSum.hasPathSum(single, 7), "single exact"); count++;
        expect(false, BinaryTreePathSum.hasPathSum(single, 0), "single mismatch"); count++;

        var root = n(5,
                n(4, n(11, n(7, null, null), n(2, null, null)), null),
                n(8, n(13, null, null), n(4, null, n(1, null, null))));
        expect(true, BinaryTreePathSum.hasPathSum(root, 22), "classic left path"); count++;
        expect(true, BinaryTreePathSum.hasPathSum(root, 26), "right leaf path"); count++;
        expect(false, BinaryTreePathSum.hasPathSum(root, 17), "internal-node sum is not enough"); count++;

        var negative = n(-2, null, n(-3, null, null));
        expect(true, BinaryTreePathSum.hasPathSum(negative, -5), "negative values"); count++;

        var zero = n(0, n(0, null, null), n(1, null, null));
        expect(true, BinaryTreePathSum.hasPathSum(zero, 0), "zero root-to-leaf"); count++;

        var extremes = n(Integer.MAX_VALUE, n(Integer.MAX_VALUE, null, null), null);
        expect(true, BinaryTreePathSum.hasPathSum(extremes, 2L * Integer.MAX_VALUE), "long target avoids overflow"); count++;

        String before = serialize(root);
        BinaryTreePathSum.hasPathSum(root, 9999);
        expect(before.equals(serialize(root)), true, "mutation"); count++;
        return count;
    }

    private static int runRandomized(int rounds, long seed) {
        Random r = new Random(seed);
        for (int i = 0; i < rounds; i++) {
            BinaryTreePathSum.Node root = randomTree(r, 0, 7);
            long target;
            if (root != null && r.nextBoolean()) {
                target = randomRootToLeafSum(root, r);
                if (r.nextInt(4) == 0) target += r.nextBoolean() ? 1 : -1;
            } else {
                target = r.nextInt(121) - 60;
            }
            String before = serialize(root);
            boolean expected = oracle(root, target);
            boolean actual = BinaryTreePathSum.hasPathSum(root, target);
            if (expected != actual) {
                throw new AssertionError("round=" + i + " target=" + target
                        + " expected=" + expected + " actual=" + actual
                        + " tree=" + before);
            }
            if (!before.equals(serialize(root))) {
                throw new AssertionError("mutation round=" + i);
            }
        }
        return rounds;
    }

    private static boolean oracle(BinaryTreePathSum.Node root, long target) {
        if (root == null) return false;
        Deque<State> stack = new ArrayDeque<>();
        stack.push(new State(root, root.value));
        while (!stack.isEmpty()) {
            State s = stack.pop();
            var node = s.node();
            long sum = s.sum();
            if (node.left == null && node.right == null && sum == target) return true;
            if (node.right != null) stack.push(new State(node.right, sum + node.right.value));
            if (node.left != null) stack.push(new State(node.left, sum + node.left.value));
        }
        return false;
    }

    private static BinaryTreePathSum.Node randomTree(Random r, int depth, int maxDepth) {
        if (depth >= maxDepth || (depth > 0 && r.nextDouble() < 0.30)) return null;
        var node = new BinaryTreePathSum.Node(r.nextInt(21) - 10);
        node.left = randomTree(r, depth + 1, maxDepth);
        node.right = randomTree(r, depth + 1, maxDepth);
        return node;
    }

    private static long randomRootToLeafSum(BinaryTreePathSum.Node root, Random r) {
        long sum = 0;
        BinaryTreePathSum.Node node = root;
        while (node != null) {
            sum += node.value;
            if (node.left == null && node.right == null) return sum;
            if (node.left == null) node = node.right;
            else if (node.right == null) node = node.left;
            else node = r.nextBoolean() ? node.left : node.right;
        }
        throw new IllegalStateException();
    }

    private static BinaryTreePathSum.Node n(int value, BinaryTreePathSum.Node left, BinaryTreePathSum.Node right) {
        var node = new BinaryTreePathSum.Node(value);
        node.left = left;
        node.right = right;
        return node;
    }

    private static String serialize(BinaryTreePathSum.Node root) {
        StringBuilder sb = new StringBuilder();
        serialize(root, sb);
        return sb.toString();
    }

    private static void serialize(BinaryTreePathSum.Node node, StringBuilder sb) {
        if (node == null) {
            sb.append('#');
            return;
        }
        sb.append('(').append(node.value).append(',');
        serialize(node.left, sb);
        sb.append(',');
        serialize(node.right, sb);
        sb.append(')');
    }

    private static void expect(boolean expected, boolean actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }
}
