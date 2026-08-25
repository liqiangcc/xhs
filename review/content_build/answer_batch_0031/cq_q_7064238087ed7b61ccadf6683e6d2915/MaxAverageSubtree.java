import java.math.BigInteger;

public final class MaxAverageSubtree {
    public static final class TreeNode {
        public final int val;
        public TreeNode left;
        public TreeNode right;
        public TreeNode(int val) { this.val = val; }
    }

    private static final class Stat {
        final long sum;
        final long count;
        Stat(long sum, long count) {
            this.sum = sum;
            this.count = count;
        }
    }

    private long bestSum;
    private long bestCount;
    private boolean hasBest;

    public double maxAverage(TreeNode root) {
        if (root == null) throw new IllegalArgumentException("root must be non-null");
        hasBest = false;
        dfs(root);
        return (double) bestSum / bestCount;
    }

    private Stat dfs(TreeNode node) {
        if (node == null) return new Stat(0L, 0L);

        Stat left = dfs(node.left);
        Stat right = dfs(node.right);
        long sum = Math.addExact(Math.addExact(left.sum, right.sum), node.val);
        long count = Math.addExact(Math.addExact(left.count, right.count), 1L);

        if (!hasBest || greater(sum, count, bestSum, bestCount)) {
            bestSum = sum;
            bestCount = count;
            hasBest = true;
        }
        return new Stat(sum, count);
    }

    static boolean greater(long aSum, long aCount, long bSum, long bCount) {
        BigInteger left = BigInteger.valueOf(aSum).multiply(BigInteger.valueOf(bCount));
        BigInteger right = BigInteger.valueOf(bSum).multiply(BigInteger.valueOf(aCount));
        return left.compareTo(right) > 0;
    }
}
