import java.util.ArrayList;
import java.util.List;

public final class BinaryTreeRightSideView {
    private BinaryTreeRightSideView() {}

    public static final class Node {
        public final int value;
        public Node left;
        public Node right;

        public Node(int value) {
            this.value = value;
        }
    }

    public static List<Integer> rightSideView(Node root) {
        List<Integer> result = new ArrayList<>();
        collectRightFirst(root, 0, result);
        return List.copyOf(result);
    }

    private static void collectRightFirst(Node node, int depth, List<Integer> result) {
        if (node == null) {
            return;
        }
        if (depth == result.size()) {
            result.add(node.value);
        }
        collectRightFirst(node.right, depth + 1, result);
        collectRightFirst(node.left, depth + 1, result);
    }
}
