import java.util.*;

public final class LevelOrderTraversalReviewerTest {
    private static final Random RNG = new Random(0x620061D4L);

    private static void fail(String message) { throw new AssertionError(message); }

    private static List<List<Integer>> oracle(LevelOrderTraversal.TreeNode root) {
        List<List<Integer>> levels = new ArrayList<>();
        oracleDfs(root, 0, levels);
        return levels;
    }

    private static void oracleDfs(LevelOrderTraversal.TreeNode node, int depth, List<List<Integer>> levels) {
        if (node == null) return;
        while (levels.size() <= depth) levels.add(new ArrayList<>());
        levels.get(depth).add(node.val);
        oracleDfs(node.left, depth + 1, levels);
        oracleDfs(node.right, depth + 1, levels);
    }

    private static void check(LevelOrderTraversal.TreeNode root, String label) {
        List<List<Integer>> expected = oracle(root);
        List<List<Integer>> actual = LevelOrderTraversal.levelOrder(root);
        if (!actual.equals(expected)) fail(label + " expected=" + expected + " actual=" + actual);
    }

    private static LevelOrderTraversal.TreeNode randomTree(int maxNodes) {
        if (maxNodes <= 0 || RNG.nextInt(6) == 0) return null;
        LevelOrderTraversal.TreeNode root = new LevelOrderTraversal.TreeNode(RNG.nextInt(9) - 4);
        ArrayDeque<LevelOrderTraversal.TreeNode> open = new ArrayDeque<>();
        open.add(root);
        int count = 1;
        while (!open.isEmpty() && count < maxNodes) {
            LevelOrderTraversal.TreeNode p = open.removeFirst();
            if (count < maxNodes && RNG.nextInt(100) < 64) {
                p.left = new LevelOrderTraversal.TreeNode(RNG.nextInt(9) - 4);
                open.addLast(p.left);
                count++;
            }
            if (count < maxNodes && RNG.nextInt(100) < 64) {
                p.right = new LevelOrderTraversal.TreeNode(RNG.nextInt(9) - 4);
                open.addLast(p.right);
                count++;
            }
        }
        return root;
    }

    public static void main(String[] args) {
        check(null, "null");
        check(new LevelOrderTraversal.TreeNode(7), "single");

        LevelOrderTraversal.TreeNode balanced = new LevelOrderTraversal.TreeNode(1);
        balanced.left = new LevelOrderTraversal.TreeNode(2);
        balanced.right = new LevelOrderTraversal.TreeNode(3);
        balanced.left.left = new LevelOrderTraversal.TreeNode(4);
        balanced.left.right = new LevelOrderTraversal.TreeNode(5);
        balanced.right.left = new LevelOrderTraversal.TreeNode(6);
        balanced.right.right = new LevelOrderTraversal.TreeNode(7);
        check(balanced, "balanced");

        LevelOrderTraversal.TreeNode sparse = new LevelOrderTraversal.TreeNode(8);
        sparse.right = new LevelOrderTraversal.TreeNode(9);
        sparse.right.left = new LevelOrderTraversal.TreeNode(10);
        sparse.right.left.right = new LevelOrderTraversal.TreeNode(11);
        check(sparse, "sparse");

        LevelOrderTraversal.TreeNode leftChain = new LevelOrderTraversal.TreeNode(3);
        leftChain.left = new LevelOrderTraversal.TreeNode(3);
        leftChain.left.left = new LevelOrderTraversal.TreeNode(3);
        check(leftChain, "left-chain-duplicates");

        LevelOrderTraversal.TreeNode rightChain = new LevelOrderTraversal.TreeNode(-1);
        rightChain.right = new LevelOrderTraversal.TreeNode(-2);
        rightChain.right.right = new LevelOrderTraversal.TreeNode(-3);
        check(rightChain, "right-chain");

        LevelOrderTraversal.TreeNode mixed = new LevelOrderTraversal.TreeNode(0);
        mixed.left = new LevelOrderTraversal.TreeNode(5);
        mixed.right = new LevelOrderTraversal.TreeNode(5);
        mixed.left.right = new LevelOrderTraversal.TreeNode(6);
        mixed.right.left = new LevelOrderTraversal.TreeNode(6);
        check(mixed, "duplicate-values-distinct-nodes");

        LevelOrderTraversal.TreeNode wide = new LevelOrderTraversal.TreeNode(1);
        wide.left = new LevelOrderTraversal.TreeNode(2);
        wide.right = new LevelOrderTraversal.TreeNode(3);
        wide.left.left = new LevelOrderTraversal.TreeNode(4);
        wide.left.right = new LevelOrderTraversal.TreeNode(5);
        wide.right.left = new LevelOrderTraversal.TreeNode(6);
        wide.right.right = new LevelOrderTraversal.TreeNode(7);
        wide.left.left.left = new LevelOrderTraversal.TreeNode(8);
        wide.right.right.right = new LevelOrderTraversal.TreeNode(9);
        check(wide, "wide-with-holes");

        for (int i = 0; i < 40000; i++) {
            check(randomTree(1 + RNG.nextInt(90)), "random-" + i);
        }
        System.out.println("PASS reviewer fixed=8 random=40000 oracle=dfs-depth null=empty duplicates=preserved sparse=preserved");
    }
}
