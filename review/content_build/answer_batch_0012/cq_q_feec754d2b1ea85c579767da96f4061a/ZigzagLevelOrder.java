import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class ZigzagLevelOrder {
    private ZigzagLevelOrder() {}

    public static final class TreeNode {
        public final int val;
        public TreeNode left;
        public TreeNode right;

        public TreeNode(int val) {
            this.val = val;
        }
    }

    public static List<List<Integer>> traverse(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) {
            return result;
        }

        ArrayDeque<TreeNode> queue = new ArrayDeque<>();
        queue.addLast(root);
        boolean leftToRight = true;

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            Integer[] level = new Integer[levelSize];

            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.removeFirst();
                int targetIndex = leftToRight ? i : levelSize - 1 - i;
                level[targetIndex] = node.val;

                if (node.left != null) {
                    queue.addLast(node.left);
                }
                if (node.right != null) {
                    queue.addLast(node.right);
                }
            }

            result.add(new ArrayList<>(Arrays.asList(level)));
            leftToRight = !leftToRight;
        }

        return result;
    }
}
