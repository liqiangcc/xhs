import java.util.List;
import java.util.Random;

public final class BinaryTreeInorderTest {
    private static int fixed = 0;

    public static void main(String[] args) {
        fixedCases();

        Random random = new Random(20260823L);
        for (int i = 0; i < 5000; i++) {
            BinaryTreeInorder.Node root = randomTree(random, 0, 8);
            String before = serialize(root);
            List<Integer> expected = BinaryTreeInorder.inorderRecursive(root);
            List<Integer> actual = BinaryTreeInorder.inorderIterative(root);
            String after = serialize(root);
            require(expected.equals(actual), "random mismatch at " + i + ": expected=" + expected + " actual=" + actual);
            require(before.equals(after), "tree mutated at random case " + i);
        }

        System.out.println("PASS fixed=" + fixed + " randomized=5000 oracle=recursive-inorder mutation=none");
    }

    private static void fixedCases() {
        check(null, List.of());

        BinaryTreeInorder.Node single = node(7);
        check(single, List.of(7));

        BinaryTreeInorder.Node balanced = node(4);
        balanced.left = node(2);
        balanced.right = node(6);
        balanced.left.left = node(1);
        balanced.left.right = node(3);
        balanced.right.left = node(5);
        balanced.right.right = node(7);
        check(balanced, List.of(1, 2, 3, 4, 5, 6, 7));

        BinaryTreeInorder.Node leftSkewed = node(4);
        leftSkewed.left = node(3);
        leftSkewed.left.left = node(2);
        leftSkewed.left.left.left = node(1);
        check(leftSkewed, List.of(1, 2, 3, 4));

        BinaryTreeInorder.Node rightSkewed = node(1);
        rightSkewed.right = node(2);
        rightSkewed.right.right = node(3);
        rightSkewed.right.right.right = node(4);
        check(rightSkewed, List.of(1, 2, 3, 4));

        BinaryTreeInorder.Node duplicates = node(2);
        duplicates.left = node(2);
        duplicates.right = node(2);
        duplicates.left.right = node(2);
        check(duplicates, List.of(2, 2, 2, 2));
    }

    private static void check(BinaryTreeInorder.Node root, List<Integer> expected) {
        String before = serialize(root);
        List<Integer> recursive = BinaryTreeInorder.inorderRecursive(root);
        List<Integer> iterative = BinaryTreeInorder.inorderIterative(root);
        String after = serialize(root);
        require(expected.equals(recursive), "fixed recursive mismatch: expected=" + expected + " actual=" + recursive);
        require(expected.equals(iterative), "fixed iterative mismatch: expected=" + expected + " actual=" + iterative);
        require(before.equals(after), "tree mutated in fixed case");
        fixed++;
    }

    private static BinaryTreeInorder.Node randomTree(Random random, int depth, int maxDepth) {
        if (depth >= maxDepth || (depth > 0 && random.nextDouble() < 0.32)) {
            return null;
        }
        BinaryTreeInorder.Node node = node(random.nextInt(11) - 5);
        node.left = randomTree(random, depth + 1, maxDepth);
        node.right = randomTree(random, depth + 1, maxDepth);
        return node;
    }

    private static BinaryTreeInorder.Node node(int value) {
        return new BinaryTreeInorder.Node(value);
    }

    private static String serialize(BinaryTreeInorder.Node root) {
        StringBuilder out = new StringBuilder();
        serialize(root, out);
        return out.toString();
    }

    private static void serialize(BinaryTreeInorder.Node node, StringBuilder out) {
        if (node == null) {
            out.append("#,");
            return;
        }
        out.append(node.value).append(',');
        serialize(node.left, out);
        serialize(node.right, out);
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
