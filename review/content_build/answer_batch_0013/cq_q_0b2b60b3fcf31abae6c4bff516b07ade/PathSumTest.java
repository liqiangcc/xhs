import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Queue;
import java.util.Random;

public final class PathSumTest {
    private static int fixedChecks;

    public static void main(String[] args) {
        checkFixedCases();
        checkRandomizedAgainstIndependentOracle();
        checkDeepIterativeChain();
        System.out.println("PASS fixed=" + fixedChecks
                + " randomized=3000 oracle=root-to-leaf-sum-enumeration deep_iterative=5000");
    }

    private static void checkFixedCases() {
        assertBoth(null, 0, false, "empty tree");

        PathSum.TreeNode single = new PathSum.TreeNode(7);
        assertBoth(single, 7, true, "single matching leaf");
        assertBoth(single, 8, false, "single non-matching leaf");

        PathSum.TreeNode classic = new PathSum.TreeNode(5);
        classic.left = new PathSum.TreeNode(4);
        classic.right = new PathSum.TreeNode(8);
        classic.left.left = new PathSum.TreeNode(11);
        classic.left.left.left = new PathSum.TreeNode(7);
        classic.left.left.right = new PathSum.TreeNode(2);
        classic.right.left = new PathSum.TreeNode(13);
        classic.right.right = new PathSum.TreeNode(4);
        classic.right.right.right = new PathSum.TreeNode(1);
        assertBoth(classic, 22, true, "root-to-leaf match");

        PathSum.TreeNode prefixOnly = new PathSum.TreeNode(1);
        prefixOnly.left = new PathSum.TreeNode(2);
        prefixOnly.left.left = new PathSum.TreeNode(4);
        assertBoth(prefixOnly, 3, false, "non-leaf prefix must not match");

        PathSum.TreeNode negative = new PathSum.TreeNode(-2);
        negative.right = new PathSum.TreeNode(-3);
        assertBoth(negative, -5, true, "negative values");
        assertBoth(negative, -2, false, "root alone is not a leaf when it has a child");
    }

    private static void checkRandomizedAgainstIndependentOracle() {
        Random random = new Random(0x0B2B60B3L);
        for (int round = 0; round < 3000; round++) {
            PathSum.TreeNode root = randomTree(random, random.nextInt(60));
            int target;
            if (root != null && round % 3 == 0) {
                List<Long> sums = enumerateRootToLeafSums(root);
                target = clampToInt(sums.get(random.nextInt(sums.size())));
            } else {
                target = random.nextInt(401) - 200;
            }

            boolean expected = oracle(root, target);
            boolean recursive = PathSum.hasPathSumRecursive(root, target);
            boolean iterative = PathSum.hasPathSumIterative(root, target);
            if (recursive != expected || iterative != expected) {
                throw new AssertionError("random round " + round
                        + " target=" + target
                        + " expected=" + expected
                        + " recursive=" + recursive
                        + " iterative=" + iterative);
            }
        }
    }

    private static void checkDeepIterativeChain() {
        PathSum.TreeNode root = new PathSum.TreeNode(1);
        PathSum.TreeNode cursor = root;
        for (int i = 1; i < 5000; i++) {
            cursor.left = new PathSum.TreeNode(1);
            cursor = cursor.left;
        }
        if (!PathSum.hasPathSumIterative(root, 5000)) {
            throw new AssertionError("deep iterative chain should match target 5000");
        }
        if (PathSum.hasPathSumIterative(root, 4999)) {
            throw new AssertionError("deep iterative chain must require the leaf");
        }
    }

    private static void assertBoth(PathSum.TreeNode root, int target, boolean expected, String label) {
        fixedChecks++;
        boolean recursive = PathSum.hasPathSumRecursive(root, target);
        boolean iterative = PathSum.hasPathSumIterative(root, target);
        if (recursive != expected || iterative != expected) {
            throw new AssertionError(label + ": expected=" + expected
                    + " recursive=" + recursive + " iterative=" + iterative);
        }
    }

    private static boolean oracle(PathSum.TreeNode root, int target) {
        if (root == null) {
            return false;
        }
        for (long sum : enumerateRootToLeafSums(root)) {
            if (sum == target) {
                return true;
            }
        }
        return false;
    }

    private static List<Long> enumerateRootToLeafSums(PathSum.TreeNode root) {
        List<Long> sums = new ArrayList<>();
        Queue<SumState> queue = new ArrayDeque<>();
        queue.add(new SumState(root, root.val));
        while (!queue.isEmpty()) {
            SumState current = queue.remove();
            PathSum.TreeNode node = current.node;
            if (node.left == null && node.right == null) {
                sums.add(current.sum);
                continue;
            }
            if (node.left != null) {
                queue.add(new SumState(node.left, current.sum + node.left.val));
            }
            if (node.right != null) {
                queue.add(new SumState(node.right, current.sum + node.right.val));
            }
        }
        return sums;
    }

    private static PathSum.TreeNode randomTree(Random random, int size) {
        if (size == 0) {
            return null;
        }
        PathSum.TreeNode root = new PathSum.TreeNode(random.nextInt(41) - 20);
        List<PathSum.TreeNode> open = new ArrayList<>();
        open.add(root);
        for (int i = 1; i < size; i++) {
            PathSum.TreeNode node = new PathSum.TreeNode(random.nextInt(41) - 20);
            while (true) {
                int index = random.nextInt(open.size());
                PathSum.TreeNode parent = open.get(index);
                boolean tryLeftFirst = random.nextBoolean();
                if (tryLeftFirst && parent.left == null) {
                    parent.left = node;
                    break;
                }
                if (!tryLeftFirst && parent.right == null) {
                    parent.right = node;
                    break;
                }
                if (parent.left == null) {
                    parent.left = node;
                    break;
                }
                if (parent.right == null) {
                    parent.right = node;
                    break;
                }
                open.remove(index);
            }
            open.add(node);
        }
        return root;
    }

    private static int clampToInt(long value) {
        if (value > Integer.MAX_VALUE || value < Integer.MIN_VALUE) {
            throw new AssertionError("generated path sum outside int range: " + value);
        }
        return (int) value;
    }

    private static final class SumState {
        final PathSum.TreeNode node;
        final long sum;

        SumState(PathSum.TreeNode node, long sum) {
            this.node = node;
            this.sum = sum;
        }
    }
}
