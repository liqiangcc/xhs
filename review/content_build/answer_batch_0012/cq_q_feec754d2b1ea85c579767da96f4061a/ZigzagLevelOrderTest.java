import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public final class ZigzagLevelOrderTest {
    private static final long SEED = 103L;

    public static void main(String[] args) {
        int boundaryCases = 0;
        boundaryCases += assertTraversal(null, List.of());
        boundaryCases += assertTraversal(node(1), List.of(List.of(1)));

        ZigzagLevelOrder.TreeNode standard = node(3);
        standard.left = node(9);
        standard.right = node(20);
        standard.right.left = node(15);
        standard.right.right = node(7);
        boundaryCases += assertTraversal(standard, List.of(
                List.of(3),
                List.of(20, 9),
                List.of(15, 7)));

        ZigzagLevelOrder.TreeNode complete = node(1);
        complete.left = node(2);
        complete.right = node(3);
        complete.left.left = node(4);
        complete.left.right = node(5);
        complete.right.left = node(6);
        complete.right.right = node(7);
        boundaryCases += assertTraversal(complete, List.of(
                List.of(1),
                List.of(3, 2),
                List.of(4, 5, 6, 7)));

        ZigzagLevelOrder.TreeNode leftSkewed = node(1);
        leftSkewed.left = node(2);
        leftSkewed.left.left = node(3);
        leftSkewed.left.left.left = node(4);
        boundaryCases += assertTraversal(leftSkewed, List.of(
                List.of(1), List.of(2), List.of(3), List.of(4)));

        ZigzagLevelOrder.TreeNode duplicates = node(5);
        duplicates.left = node(5);
        duplicates.right = node(5);
        boundaryCases += assertTraversal(duplicates, List.of(List.of(5), List.of(5, 5)));

        Random random = new Random(SEED);
        int randomCases = 3000;
        for (int i = 0; i < randomCases; i++) {
            ZigzagLevelOrder.TreeNode root = randomTree(random, 1 + random.nextInt(80));
            List<List<Integer>> expected = dfsOracle(root);
            List<List<Integer>> actual = ZigzagLevelOrder.traverse(root);
            if (!expected.equals(actual)) {
                throw new AssertionError("random mismatch case=" + i
                        + " expected=" + expected + " actual=" + actual);
            }
        }

        System.out.println("PASS random_cases=" + randomCases
                + " seed=" + SEED
                + " official_examples=3"
                + " boundary_cases=" + boundaryCases);
    }

    private static int assertTraversal(ZigzagLevelOrder.TreeNode root, List<List<Integer>> expected) {
        List<List<Integer>> actual = ZigzagLevelOrder.traverse(root);
        if (!expected.equals(actual)) {
            throw new AssertionError("expected=" + expected + " actual=" + actual);
        }
        return 1;
    }

    private static ZigzagLevelOrder.TreeNode randomTree(Random random, int nodeCount) {
        ZigzagLevelOrder.TreeNode root = node(random.nextInt(201) - 100);
        List<ZigzagLevelOrder.TreeNode> candidates = new ArrayList<>();
        candidates.add(root);

        for (int i = 1; i < nodeCount; i++) {
            ZigzagLevelOrder.TreeNode child = node(random.nextInt(201) - 100);
            while (true) {
                ZigzagLevelOrder.TreeNode parent = candidates.get(random.nextInt(candidates.size()));
                boolean chooseLeft = random.nextBoolean();
                if (chooseLeft && parent.left == null) {
                    parent.left = child;
                    break;
                }
                if (!chooseLeft && parent.right == null) {
                    parent.right = child;
                    break;
                }
                if (parent.left == null) {
                    parent.left = child;
                    break;
                }
                if (parent.right == null) {
                    parent.right = child;
                    break;
                }
                candidates.remove(parent);
            }
            candidates.add(child);
        }
        return root;
    }

    private static List<List<Integer>> dfsOracle(ZigzagLevelOrder.TreeNode root) {
        List<List<Integer>> levels = new ArrayList<>();
        collect(root, 0, levels);
        for (int depth = 1; depth < levels.size(); depth += 2) {
            Collections.reverse(levels.get(depth));
        }
        return levels;
    }

    private static void collect(ZigzagLevelOrder.TreeNode node, int depth, List<List<Integer>> levels) {
        if (node == null) {
            return;
        }
        if (levels.size() == depth) {
            levels.add(new ArrayList<>());
        }
        levels.get(depth).add(node.val);
        collect(node.left, depth + 1, levels);
        collect(node.right, depth + 1, levels);
    }

    private static ZigzagLevelOrder.TreeNode node(int value) {
        return new ZigzagLevelOrder.TreeNode(value);
    }
}
