import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Queue;
import java.util.Random;

public final class BinaryTreeDiameterTest {
    public static void main(String[] args) {
        expect(null, 0, "empty");

        BinaryTreeDiameter.TreeNode single = new BinaryTreeDiameter.TreeNode(1);
        expect(single, 0, "single");

        BinaryTreeDiameter.TreeNode chain = chain(6);
        expect(chain, 5, "six-node chain");

        BinaryTreeDiameter.TreeNode balanced = node(1,
                node(2, node(4, null, null), node(5, null, null)),
                node(3, null, null));
        expect(balanced, 3, "balanced sample");

        BinaryTreeDiameter.TreeNode notThroughRoot = node(1,
                node(2,
                        node(4, node(6, null, null), null),
                        node(5, null, node(7, null, null))),
                node(3, null, null));
        expect(notThroughRoot, 4, "subtree diameter");

        Random random = new Random(550106L);
        int randomCases = 3000;
        for (int i = 0; i < randomCases; i++) {
            int size = random.nextInt(41);
            BinaryTreeDiameter.TreeNode root = randomTree(size, random);
            int expected = bruteForceDiameter(root);
            int actual = BinaryTreeDiameter.diameterEdges(root);
            if (expected != actual) {
                throw new AssertionError("random mismatch case=" + i
                        + " size=" + size + " expected=" + expected + " actual=" + actual);
            }
        }

        System.out.println("PASS fixed_cases=5 random_cases=3000 max_nodes=40 seed=550106");
    }

    private static void expect(BinaryTreeDiameter.TreeNode root, int expected, String label) {
        int actual = BinaryTreeDiameter.diameterEdges(root);
        if (actual != expected) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    private static BinaryTreeDiameter.TreeNode chain(int size) {
        if (size == 0) return null;
        BinaryTreeDiameter.TreeNode root = new BinaryTreeDiameter.TreeNode(0);
        BinaryTreeDiameter.TreeNode current = root;
        for (int i = 1; i < size; i++) {
            current.left = new BinaryTreeDiameter.TreeNode(i);
            current = current.left;
        }
        return root;
    }

    private static BinaryTreeDiameter.TreeNode node(
            int value,
            BinaryTreeDiameter.TreeNode left,
            BinaryTreeDiameter.TreeNode right) {
        BinaryTreeDiameter.TreeNode node = new BinaryTreeDiameter.TreeNode(value);
        node.left = left;
        node.right = right;
        return node;
    }

    private static BinaryTreeDiameter.TreeNode randomTree(int size, Random random) {
        if (size == 0) return null;
        List<BinaryTreeDiameter.TreeNode> nodes = new ArrayList<>();
        BinaryTreeDiameter.TreeNode root = new BinaryTreeDiameter.TreeNode(0);
        nodes.add(root);

        for (int value = 1; value < size; value++) {
            BinaryTreeDiameter.TreeNode child = new BinaryTreeDiameter.TreeNode(value);
            while (true) {
                BinaryTreeDiameter.TreeNode parent = nodes.get(random.nextInt(nodes.size()));
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
            }
            nodes.add(child);
        }
        return root;
    }

    private static int bruteForceDiameter(BinaryTreeDiameter.TreeNode root) {
        if (root == null) return 0;

        List<BinaryTreeDiameter.TreeNode> nodes = new ArrayList<>();
        Map<BinaryTreeDiameter.TreeNode, List<BinaryTreeDiameter.TreeNode>> graph =
                new IdentityHashMap<>();
        buildGraph(root, null, nodes, graph);

        int best = 0;
        for (BinaryTreeDiameter.TreeNode start : nodes) {
            Map<BinaryTreeDiameter.TreeNode, Integer> distance = new IdentityHashMap<>();
            Queue<BinaryTreeDiameter.TreeNode> queue = new ArrayDeque<>();
            distance.put(start, 0);
            queue.add(start);

            while (!queue.isEmpty()) {
                BinaryTreeDiameter.TreeNode current = queue.remove();
                int currentDistance = distance.get(current);
                best = Math.max(best, currentDistance);
                for (BinaryTreeDiameter.TreeNode next : graph.get(current)) {
                    if (!distance.containsKey(next)) {
                        distance.put(next, currentDistance + 1);
                        queue.add(next);
                    }
                }
            }
        }
        return best;
    }

    private static void buildGraph(
            BinaryTreeDiameter.TreeNode node,
            BinaryTreeDiameter.TreeNode parent,
            List<BinaryTreeDiameter.TreeNode> nodes,
            Map<BinaryTreeDiameter.TreeNode, List<BinaryTreeDiameter.TreeNode>> graph) {
        if (node == null) return;
        nodes.add(node);
        graph.computeIfAbsent(node, ignored -> new ArrayList<>());
        if (parent != null) {
            graph.get(node).add(parent);
            graph.get(parent).add(node);
        }
        buildGraph(node.left, node, nodes, graph);
        buildGraph(node.right, node, nodes, graph);
    }
}
