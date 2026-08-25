import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class MaxAverageSubtreeTest {
    private static final double EPS = 1e-12;

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static long[] sumCount(MaxAverageSubtree.TreeNode node) {
        if (node == null) return new long[]{0L, 0L};
        long[] l = sumCount(node.left);
        long[] r = sumCount(node.right);
        return new long[]{Math.addExact(Math.addExact(l[0], r[0]), node.val), Math.addExact(Math.addExact(l[1], r[1]), 1L)};
    }

    private static void collect(MaxAverageSubtree.TreeNode node, List<MaxAverageSubtree.TreeNode> out) {
        if (node == null) return;
        out.add(node);
        collect(node.left, out);
        collect(node.right, out);
    }

    private static double oracle(MaxAverageSubtree.TreeNode root) {
        List<MaxAverageSubtree.TreeNode> nodes = new ArrayList<>();
        collect(root, nodes);
        double best = Double.NEGATIVE_INFINITY;
        for (MaxAverageSubtree.TreeNode node : nodes) {
            long[] sc = sumCount(node);
            best = Math.max(best, (double) sc[0] / sc[1]);
        }
        return best;
    }

    private static MaxAverageSubtree.TreeNode randomTree(Random rnd, int n) {
        if (n == 0) return null;
        List<MaxAverageSubtree.TreeNode> nodes = new ArrayList<>();
        for (int i = 0; i < n; i++) nodes.add(new MaxAverageSubtree.TreeNode(rnd.nextInt(101) - 50));
        for (int i = 1; i < n; i++) {
            while (true) {
                int p = rnd.nextInt(i);
                MaxAverageSubtree.TreeNode parent = nodes.get(p);
                if (parent.left == null && parent.right == null) {
                    if (rnd.nextBoolean()) parent.left = nodes.get(i); else parent.right = nodes.get(i);
                    break;
                }
                if (parent.left == null) { parent.left = nodes.get(i); break; }
                if (parent.right == null) { parent.right = nodes.get(i); break; }
            }
        }
        return nodes.get(0);
    }

    public static void main(String[] args) {
        MaxAverageSubtree solver = new MaxAverageSubtree();

        MaxAverageSubtree.TreeNode single = new MaxAverageSubtree.TreeNode(-7);
        require(Math.abs(solver.maxAverage(single) + 7.0) < EPS, "single negative node");

        MaxAverageSubtree.TreeNode root = new MaxAverageSubtree.TreeNode(-5);
        root.left = new MaxAverageSubtree.TreeNode(-2);
        root.right = new MaxAverageSubtree.TreeNode(-8);
        require(Math.abs(solver.maxAverage(root) + 2.0) < EPS, "all-negative tree must choose -2 leaf");

        MaxAverageSubtree.TreeNode mixed = new MaxAverageSubtree.TreeNode(5);
        mixed.left = new MaxAverageSubtree.TreeNode(6);
        mixed.right = new MaxAverageSubtree.TreeNode(1);
        mixed.right.left = new MaxAverageSubtree.TreeNode(20);
        require(Math.abs(solver.maxAverage(mixed) - 20.0) < EPS, "mixed tree max leaf");

        boolean threw = false;
        try { solver.maxAverage(null); } catch (IllegalArgumentException expected) { threw = true; }
        require(threw, "null root contract");

        require(MaxAverageSubtree.greater(Long.MAX_VALUE, 2, Long.MAX_VALUE - 1, 2), "exact fraction comparator high positive");
        require(MaxAverageSubtree.greater(-1, 3, -1, 2), "negative fraction ordering");

        Random rnd = new Random(7064238087L);
        for (int i = 0; i < 3000; i++) {
            MaxAverageSubtree.TreeNode t = randomTree(rnd, 1 + rnd.nextInt(20));
            double expected = oracle(t);
            double actual = solver.maxAverage(t);
            require(Math.abs(expected - actual) < EPS, "random oracle mismatch round=" + i + " expected=" + expected + " actual=" + actual);
        }

        System.out.println("PASS single-negative=yes all-negative=yes mixed=yes null-contract=yes exact-fraction=yes random-oracle=3000");
    }
}
