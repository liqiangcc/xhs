final class RootToLeafNumberSum {
    static final class TreeNode {
        final int val;
        TreeNode left;
        TreeNode right;
        TreeNode(int val) { this.val = val; }
    }

    static long sumRootToLeafNumbers(TreeNode root) {
        if (root == null) return 0L;
        return dfs(root, 0L);
    }

    private static long dfs(TreeNode node, long prefix) {
        if (node.val < 0 || node.val > 9) {
            throw new IllegalArgumentException("node value must be a decimal digit");
        }
        long current = Math.addExact(Math.multiplyExact(prefix, 10L), node.val);
        if (node.left == null && node.right == null) return current;
        long left = node.left == null ? 0L : dfs(node.left, current);
        long right = node.right == null ? 0L : dfs(node.right, current);
        return Math.addExact(left, right);
    }
}
