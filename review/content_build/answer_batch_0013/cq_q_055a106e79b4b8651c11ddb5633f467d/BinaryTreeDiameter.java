public final class BinaryTreeDiameter {
    public static final class TreeNode {
        public final int value;
        public TreeNode left;
        public TreeNode right;

        public TreeNode(int value) {
            this.value = value;
        }
    }

    private BinaryTreeDiameter() {}

    public static int diameterEdges(TreeNode root) {
        int[] best = {0};
        depthInNodes(root, best);
        return best[0];
    }

    private static int depthInNodes(TreeNode node, int[] best) {
        if (node == null) {
            return 0;
        }
        int leftDepth = depthInNodes(node.left, best);
        int rightDepth = depthInNodes(node.right, best);
        best[0] = Math.max(best[0], leftDepth + rightDepth);
        return 1 + Math.max(leftDepth, rightDepth);
    }
}
