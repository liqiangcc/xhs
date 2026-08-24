import java.util.ArrayDeque;
import java.util.Deque;

public final class MirrorBinaryTree {
    private MirrorBinaryTree() {}

    public static final class Node {
        public final int value;
        public Node left;
        public Node right;

        public Node(int value) {
            this.value = value;
        }

        public Node(int value, Node left, Node right) {
            this.value = value;
            this.left = left;
            this.right = right;
        }
    }

    public static Node mirrorRecursive(Node root) {
        if (root == null) {
            return null;
        }
        Node mirroredLeft = mirrorRecursive(root.right);
        Node mirroredRight = mirrorRecursive(root.left);
        root.left = mirroredLeft;
        root.right = mirroredRight;
        return root;
    }

    public static Node mirrorIterative(Node root) {
        if (root == null) {
            return null;
        }
        Deque<Node> stack = new ArrayDeque<>();
        stack.push(root);
        while (!stack.isEmpty()) {
            Node node = stack.pop();
            Node tmp = node.left;
            node.left = node.right;
            node.right = tmp;

            if (node.left != null) {
                stack.push(node.left);
            }
            if (node.right != null) {
                stack.push(node.right);
            }
        }
        return root;
    }
}
