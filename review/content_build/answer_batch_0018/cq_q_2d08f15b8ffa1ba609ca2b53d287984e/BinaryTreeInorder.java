import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public final class BinaryTreeInorder {
    private BinaryTreeInorder() {}

    public static final class Node {
        public final int value;
        public Node left;
        public Node right;

        public Node(int value) {
            this.value = value;
        }
    }

    public static List<Integer> inorderIterative(Node root) {
        List<Integer> result = new ArrayList<>();
        Deque<Node> stack = new ArrayDeque<>();
        Node current = root;

        while (current != null || !stack.isEmpty()) {
            while (current != null) {
                stack.push(current);
                current = current.left;
            }
            Node node = stack.pop();
            result.add(node.value);
            current = node.right;
        }
        return result;
    }

    public static List<Integer> inorderRecursive(Node root) {
        List<Integer> result = new ArrayList<>();
        appendRecursive(root, result);
        return result;
    }

    private static void appendRecursive(Node node, List<Integer> out) {
        if (node == null) {
            return;
        }
        appendRecursive(node.left, out);
        out.add(node.value);
        appendRecursive(node.right, out);
    }
}
