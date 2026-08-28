import java.util.ArrayList;
import java.util.List;

public final class BinaryTreePaths {
    public static final class TreeNode {
        final int val;
        TreeNode left;
        TreeNode right;

        public TreeNode(int val) {
            this.val = val;
        }
    }

    public static List<List<Integer>> allRootToLeafPaths(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) {
            return result;
        }
        dfs(root, new ArrayList<>(), result);
        return result;
    }

    private static void dfs(TreeNode node, List<Integer> path, List<List<Integer>> result) {
        path.add(node.val);
        if (node.left == null && node.right == null) {
            result.add(new ArrayList<>(path));
        } else {
            if (node.left != null) {
                dfs(node.left, path, result);
            }
            if (node.right != null) {
                dfs(node.right, path, result);
            }
        }
        path.remove(path.size() - 1);
    }
}
