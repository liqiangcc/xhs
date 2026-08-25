import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public final class IterativeBinaryTreeTraversal {
    public static final class Node {
        public final int value;
        public Node left;
        public Node right;
        public Node(int value) { this.value = value; }
    }

    public static List<Integer> preorder(Node root) {
        List<Integer> out = new ArrayList<>();
        if (root == null) return out;
        Deque<Node> stack = new ArrayDeque<>();
        stack.push(root);
        while (!stack.isEmpty()) {
            Node node = stack.pop();
            out.add(node.value);
            if (node.right != null) stack.push(node.right);
            if (node.left != null) stack.push(node.left);
        }
        return out;
    }

    public static List<Integer> inorder(Node root) {
        List<Integer> out = new ArrayList<>();
        Deque<Node> stack = new ArrayDeque<>();
        Node current = root;
        while (current != null || !stack.isEmpty()) {
            while (current != null) {
                stack.push(current);
                current = current.left;
            }
            Node node = stack.pop();
            out.add(node.value);
            current = node.right;
        }
        return out;
    }

    public static List<Integer> postorder(Node root) {
        List<Integer> out = new ArrayList<>();
        Deque<Node> stack = new ArrayDeque<>();
        Node current = root;
        Node lastVisited = null;
        while (current != null || !stack.isEmpty()) {
            if (current != null) {
                stack.push(current);
                current = current.left;
            } else {
                Node peek = stack.peek();
                if (peek.right != null && lastVisited != peek.right) {
                    current = peek.right;
                } else {
                    out.add(peek.value);
                    lastVisited = stack.pop();
                }
            }
        }
        return out;
    }
}
