import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class LevelOrderTraversalTest {
    private static final Random RNG = new Random(0x620061L);

    private static void assertEquals(Object expected, Object actual, String label) {
        if (!expected.equals(actual)) throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
    }

    private static List<List<Integer>> oracle(LevelOrderTraversal.TreeNode root) {
        List<List<Integer>> out = new ArrayList<>();
        dfs(root, 0, out);
        return out;
    }

    private static void dfs(LevelOrderTraversal.TreeNode node, int depth, List<List<Integer>> out) {
        if (node == null) return;
        if (out.size() == depth) out.add(new ArrayList<>());
        out.get(depth).add(node.val);
        dfs(node.left, depth + 1, out);
        dfs(node.right, depth + 1, out);
    }

    private static LevelOrderTraversal.TreeNode n(int value) { return new LevelOrderTraversal.TreeNode(value); }

    private static LevelOrderTraversal.TreeNode randomTree(int depth) {
        if (depth > 8 || (depth > 0 && RNG.nextInt(100) < 28)) return null;
        LevelOrderTraversal.TreeNode node = n(RNG.nextInt(11) - 5);
        node.left = randomTree(depth + 1);
        node.right = randomTree(depth + 1);
        return node;
    }

    public static void main(String[] args) {
        assertEquals(List.of(), LevelOrderTraversal.levelOrder(null), "null");
        assertEquals(List.of(List.of(7)), LevelOrderTraversal.levelOrder(n(7)), "single");

        LevelOrderTraversal.TreeNode balanced = n(1);
        balanced.left = n(2); balanced.right = n(3);
        balanced.left.left = n(4); balanced.left.right = n(5); balanced.right.right = n(6);
        assertEquals(List.of(List.of(1), List.of(2, 3), List.of(4, 5, 6)), LevelOrderTraversal.levelOrder(balanced), "balanced");

        LevelOrderTraversal.TreeNode left = n(1); left.left = n(2); left.left.left = n(3);
        assertEquals(List.of(List.of(1), List.of(2), List.of(3)), LevelOrderTraversal.levelOrder(left), "left-chain");

        LevelOrderTraversal.TreeNode right = n(1); right.right = n(2); right.right.right = n(3);
        assertEquals(List.of(List.of(1), List.of(2), List.of(3)), LevelOrderTraversal.levelOrder(right), "right-chain");

        LevelOrderTraversal.TreeNode sparse = n(9); sparse.left = n(8); sparse.right = n(7); sparse.left.right = n(6); sparse.right.left = n(5);
        assertEquals(List.of(List.of(9), List.of(8, 7), List.of(6, 5)), LevelOrderTraversal.levelOrder(sparse), "sparse-order");

        LevelOrderTraversal.TreeNode dup = n(1); dup.left = n(1); dup.right = n(1);
        assertEquals(List.of(List.of(1), List.of(1, 1)), LevelOrderTraversal.levelOrder(dup), "duplicates");

        for (int i = 0; i < 30000; i++) {
            LevelOrderTraversal.TreeNode root = randomTree(0);
            assertEquals(oracle(root), LevelOrderTraversal.levelOrder(root), "random-" + i);
        }
        System.out.println("PASS fixed=7 random=30000 oracle=dfs-depth null=empty duplicates=preserved levels=preserved");
    }
}
