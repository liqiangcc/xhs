import java.util.ArrayDeque;
import java.util.Deque;

public final class TreeEquality {
    private TreeEquality() {}

    public static final class Node {
        public final int value;
        public Node left;
        public Node right;

        public Node(int value) {
            this.value = value;
        }
    }

    public static boolean sameTree(Node a, Node b) {
        if (a == null || b == null) {
            return a == b;
        }
        if (a.value != b.value) {
            return false;
        }
        return sameTree(a.left, b.left) && sameTree(a.right, b.right);
    }

    static boolean bfsOracle(Node a, Node b) {
        Deque<NodePair> queue = new ArrayDeque<>();
        queue.addLast(new NodePair(a, b));
        while (!queue.isEmpty()) {
            NodePair pair = queue.removeFirst();
            Node x = pair.a;
            Node y = pair.b;
            if (x == null || y == null) {
                if (x != y) {
                    return false;
                }
                continue;
            }
            if (x.value != y.value) {
                return false;
            }
            queue.addLast(new NodePair(x.left, y.left));
            queue.addLast(new NodePair(x.right, y.right));
        }
        return true;
    }

    private record NodePair(Node a, Node b) {}
}
