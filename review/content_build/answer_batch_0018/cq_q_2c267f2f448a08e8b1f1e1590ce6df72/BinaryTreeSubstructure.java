public final class BinaryTreeSubstructure {
    private BinaryTreeSubstructure() {}

    public static final class Node {
        public final int value;
        public Node left;
        public Node right;

        public Node(int value) {
            this.value = value;
        }
    }

    public static boolean isSubstructure(Node a, Node b) {
        if (a == null || b == null) {
            return false;
        }
        return matchesFrom(a, b)
                || isSubstructure(a.left, b)
                || isSubstructure(a.right, b);
    }

    private static boolean matchesFrom(Node a, Node b) {
        if (b == null) {
            return true;
        }
        if (a == null || a.value != b.value) {
            return false;
        }
        return matchesFrom(a.left, b.left) && matchesFrom(a.right, b.right);
    }
}
