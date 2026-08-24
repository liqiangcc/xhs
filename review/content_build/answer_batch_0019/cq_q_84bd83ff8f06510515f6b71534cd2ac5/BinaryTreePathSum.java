public final class BinaryTreePathSum {
    public static final class Node {
        public final int value;
        public Node left;
        public Node right;

        public Node(int value) {
            this.value = value;
        }
    }

    private BinaryTreePathSum() {}

    /**
     * Candidate contract: determine whether there exists a root-to-leaf path
     * whose node values sum exactly to target. A null root has no such path.
     * Inputs are not mutated.
     */
    public static boolean hasPathSum(Node root, long target) {
        if (root == null) {
            return false;
        }
        long remaining = target - root.value;
        if (root.left == null && root.right == null) {
            return remaining == 0L;
        }
        return hasPathSum(root.left, remaining)
                || hasPathSum(root.right, remaining);
    }
}
