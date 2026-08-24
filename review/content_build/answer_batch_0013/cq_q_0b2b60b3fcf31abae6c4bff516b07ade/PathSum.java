import java.util.ArrayDeque;
import java.util.Deque;

public final class PathSum {
    public static final class TreeNode {
        final int val;
        TreeNode left;
        TreeNode right;

        TreeNode(int val) {
            this.val = val;
        }
    }

    public static boolean hasPathSumRecursive(TreeNode root, int targetSum) {
        return hasPathSumRecursive(root, (long) targetSum);
    }

    private static boolean hasPathSumRecursive(TreeNode node, long remaining) {
        if (node == null) {
            return false;
        }

        long next = remaining - node.val;
        if (node.left == null && node.right == null) {
            return next == 0L;
        }
        return hasPathSumRecursive(node.left, next)
                || hasPathSumRecursive(node.right, next);
    }

    public static boolean hasPathSumIterative(TreeNode root, int targetSum) {
        if (root == null) {
            return false;
        }

        Deque<State> stack = new ArrayDeque<>();
        stack.push(new State(root, (long) targetSum));
        while (!stack.isEmpty()) {
            State current = stack.pop();
            TreeNode node = current.node;
            long next = current.remaining - node.val;

            if (node.left == null && node.right == null && next == 0L) {
                return true;
            }
            if (node.right != null) {
                stack.push(new State(node.right, next));
            }
            if (node.left != null) {
                stack.push(new State(node.left, next));
            }
        }
        return false;
    }

    private static final class State {
        final TreeNode node;
        final long remaining;

        State(TreeNode node, long remaining) {
            this.node = node;
            this.remaining = remaining;
        }
    }
}
