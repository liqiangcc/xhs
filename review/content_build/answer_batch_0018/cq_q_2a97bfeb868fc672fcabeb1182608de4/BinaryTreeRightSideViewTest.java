import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Random;

public final class BinaryTreeRightSideViewTest {
    private static int fixedChecks = 0;

    public static void main(String[] args) {
        check(null, List.of());
        check(n(7), List.of(7));

        BinaryTreeRightSideView.Node full = n(1);
        full.left = n(2); full.right = n(3);
        full.left.left = n(4); full.left.right = n(5);
        full.right.left = n(6); full.right.right = n(7);
        check(full, List.of(1, 3, 7));

        BinaryTreeRightSideView.Node right = n(1);
        right.right = n(2); right.right.right = n(3); right.right.right.right = n(4);
        check(right, List.of(1, 2, 3, 4));

        BinaryTreeRightSideView.Node left = n(1);
        left.left = n(2); left.left.left = n(3); left.left.left.left = n(4);
        check(left, List.of(1, 2, 3, 4));

        BinaryTreeRightSideView.Node gap = n(1);
        gap.left = n(2); gap.right = n(3);
        gap.left.right = n(5);
        gap.right.left = n(4);
        gap.left.right.right = n(6);
        check(gap, List.of(1, 3, 4, 6));

        BinaryTreeRightSideView.Node duplicate = n(9);
        duplicate.left = n(9); duplicate.right = n(9);
        duplicate.left.right = n(9);
        check(duplicate, List.of(9, 9, 9));

        BinaryTreeRightSideView.Node mixed = n(10);
        mixed.left = n(-1); mixed.right = n(20);
        mixed.left.left = n(30);
        mixed.right.left = n(15);
        mixed.right.left.left = n(17);
        check(mixed, List.of(10, 20, 15, 17));

        Random random = new Random(0x2a97bfebL);
        int randomized = 5000;
        for (int iteration = 0; iteration < randomized; iteration++) {
            BinaryTreeRightSideView.Node root = randomTree(random, random.nextInt(61));
            String before = serialize(root);
            List<Integer> expected = oracle(root);
            List<Integer> actual = BinaryTreeRightSideView.rightSideView(root);
            String after = serialize(root);
            if (!actual.equals(expected)) {
                throw new AssertionError("randomized mismatch at iteration " + iteration
                        + " expected=" + expected + " actual=" + actual + " tree=" + before);
            }
            if (!before.equals(after)) {
                throw new AssertionError("input tree mutated at iteration " + iteration);
            }
        }

        System.out.println("PASS fixed=" + fixedChecks
                + " randomized=" + randomized
                + " oracle=bfs-last-per-level order=top-down mutation=none");
    }

    private static BinaryTreeRightSideView.Node n(int value) {
        return new BinaryTreeRightSideView.Node(value);
    }

    private static void check(BinaryTreeRightSideView.Node root, List<Integer> expected) {
        fixedChecks++;
        String before = serialize(root);
        List<Integer> actual = BinaryTreeRightSideView.rightSideView(root);
        if (!actual.equals(expected)) {
            throw new AssertionError("fixed mismatch expected=" + expected + " actual=" + actual);
        }
        if (!actual.equals(oracle(root))) {
            throw new AssertionError("fixed oracle mismatch expected=" + oracle(root) + " actual=" + actual);
        }
        if (!before.equals(serialize(root))) {
            throw new AssertionError("fixed input tree mutated");
        }
    }

    private static List<Integer> oracle(BinaryTreeRightSideView.Node root) {
        if (root == null) {
            return List.of();
        }
        List<Integer> result = new ArrayList<>();
        Deque<BinaryTreeRightSideView.Node> queue = new ArrayDeque<>();
        queue.add(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            int last = 0;
            for (int i = 0; i < levelSize; i++) {
                BinaryTreeRightSideView.Node node = queue.remove();
                last = node.value;
                if (node.left != null) queue.add(node.left);
                if (node.right != null) queue.add(node.right);
            }
            result.add(last);
        }
        return List.copyOf(result);
    }

    private static BinaryTreeRightSideView.Node randomTree(Random random, int size) {
        if (size == 0) {
            return null;
        }
        BinaryTreeRightSideView.Node root = n(random.nextInt(41) - 20);
        List<BinaryTreeRightSideView.Node> open = new ArrayList<>();
        open.add(root);
        int created = 1;
        while (created < size) {
            int parentIndex = random.nextInt(open.size());
            BinaryTreeRightSideView.Node parent = open.get(parentIndex);
            boolean chooseLeft = random.nextBoolean();
            if (parent.left != null && parent.right != null) {
                open.remove(parentIndex);
                continue;
            }
            BinaryTreeRightSideView.Node child = n(random.nextInt(41) - 20);
            if ((chooseLeft && parent.left == null) || parent.right != null) {
                parent.left = child;
            } else {
                parent.right = child;
            }
            if (parent.left != null && parent.right != null) {
                open.remove(parentIndex);
            }
            open.add(child);
            created++;
        }
        return root;
    }

    private static String serialize(BinaryTreeRightSideView.Node node) {
        StringBuilder out = new StringBuilder();
        serialize(node, out);
        return out.toString();
    }

    private static void serialize(BinaryTreeRightSideView.Node node, StringBuilder out) {
        if (node == null) {
            out.append('#');
            return;
        }
        out.append('(').append(node.value).append(' ');
        serialize(node.left, out);
        out.append(' ');
        serialize(node.right, out);
        out.append(')');
    }
}
