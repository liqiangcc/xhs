import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class MirrorBinaryTreeTest {
    private static int fixedChecks;
    private static int randomizedChecks;

    public static void main(String[] args) {
        testNull();
        testSingleNode();
        testAsymmetricTreeRecursive();
        testAsymmetricTreeIterative();
        testDoubleMirrorRestoresTree();
        testRecursiveAndIterativeAgreeOnRandomTrees();
        testDeepSkewWithIterativeMirror();
        System.out.printf("PASS fixed=%d randomized=%d oracle=structural-mirror involution=true%n",
                fixedChecks, randomizedChecks);
    }

    private static void testNull() {
        assertTrue(MirrorBinaryTree.mirrorRecursive(null) == null, "recursive null");
        assertTrue(MirrorBinaryTree.mirrorIterative(null) == null, "iterative null");
        fixedChecks += 2;
    }

    private static void testSingleNode() {
        MirrorBinaryTree.Node node = new MirrorBinaryTree.Node(7);
        assertTrue(MirrorBinaryTree.mirrorRecursive(node) == node, "recursive returns same root");
        assertEquals("7,#,#", serialize(node), "single recursive");
        assertTrue(MirrorBinaryTree.mirrorIterative(node) == node, "iterative returns same root");
        assertEquals("7,#,#", serialize(node), "single iterative");
        fixedChecks += 4;
    }

    private static void testAsymmetricTreeRecursive() {
        MirrorBinaryTree.Node root = sampleTree();
        MirrorBinaryTree.Node originalRoot = root;
        MirrorBinaryTree.mirrorRecursive(root);
        assertTrue(root == originalRoot, "recursive mutates in place");
        assertEquals("1,3,6,#,#,5,#,#,2,4,#,#,#", serialize(root), "recursive asymmetric mirror");
        fixedChecks += 2;
    }

    private static void testAsymmetricTreeIterative() {
        MirrorBinaryTree.Node root = sampleTree();
        MirrorBinaryTree.Node originalRoot = root;
        MirrorBinaryTree.mirrorIterative(root);
        assertTrue(root == originalRoot, "iterative mutates in place");
        assertEquals("1,3,6,#,#,5,#,#,2,4,#,#,#", serialize(root), "iterative asymmetric mirror");
        fixedChecks += 2;
    }

    private static void testDoubleMirrorRestoresTree() {
        MirrorBinaryTree.Node recursive = sampleTree();
        String beforeRecursive = serialize(recursive);
        MirrorBinaryTree.mirrorRecursive(recursive);
        MirrorBinaryTree.mirrorRecursive(recursive);
        assertEquals(beforeRecursive, serialize(recursive), "recursive involution");

        MirrorBinaryTree.Node iterative = sampleTree();
        String beforeIterative = serialize(iterative);
        MirrorBinaryTree.mirrorIterative(iterative);
        MirrorBinaryTree.mirrorIterative(iterative);
        assertEquals(beforeIterative, serialize(iterative), "iterative involution");
        fixedChecks += 2;
    }

    private static void testRecursiveAndIterativeAgreeOnRandomTrees() {
        Random random = new Random(0x21A9060BL);
        for (int i = 0; i < 4000; i++) {
            MirrorBinaryTree.Node source = randomTree(random, 0, 8);
            MirrorBinaryTree.Node recursive = copy(source);
            MirrorBinaryTree.Node iterative = copy(source);
            MirrorBinaryTree.mirrorRecursive(recursive);
            MirrorBinaryTree.mirrorIterative(iterative);
            String expected = serializeMirrorOracle(source);
            assertEquals(expected, serialize(recursive), "random recursive " + i);
            assertEquals(expected, serialize(iterative), "random iterative " + i);
            randomizedChecks += 2;
        }
    }

    private static void testDeepSkewWithIterativeMirror() {
        MirrorBinaryTree.Node root = new MirrorBinaryTree.Node(0);
        MirrorBinaryTree.Node cursor = root;
        for (int i = 1; i <= 20_000; i++) {
            cursor.left = new MirrorBinaryTree.Node(i);
            cursor = cursor.left;
        }
        MirrorBinaryTree.mirrorIterative(root);
        cursor = root;
        for (int i = 1; i <= 20_000; i++) {
            assertTrue(cursor.left == null, "deep skew has no left child at " + i);
            assertTrue(cursor.right != null && cursor.right.value == i, "deep skew right chain at " + i);
            cursor = cursor.right;
        }
        assertTrue(cursor.left == null && cursor.right == null, "deep skew leaf");
        fixedChecks += 40_001;
    }

    private static MirrorBinaryTree.Node sampleTree() {
        MirrorBinaryTree.Node n4 = new MirrorBinaryTree.Node(4);
        MirrorBinaryTree.Node n5 = new MirrorBinaryTree.Node(5);
        MirrorBinaryTree.Node n6 = new MirrorBinaryTree.Node(6);
        MirrorBinaryTree.Node n2 = new MirrorBinaryTree.Node(2, null, n4);
        MirrorBinaryTree.Node n3 = new MirrorBinaryTree.Node(3, n5, n6);
        return new MirrorBinaryTree.Node(1, n2, n3);
    }

    private static MirrorBinaryTree.Node randomTree(Random random, int depth, int maxDepth) {
        if (depth >= maxDepth || (depth > 0 && random.nextDouble() < 0.32)) {
            return null;
        }
        MirrorBinaryTree.Node node = new MirrorBinaryTree.Node(random.nextInt(21) - 10);
        node.left = randomTree(random, depth + 1, maxDepth);
        node.right = randomTree(random, depth + 1, maxDepth);
        return node;
    }

    private static MirrorBinaryTree.Node copy(MirrorBinaryTree.Node node) {
        if (node == null) {
            return null;
        }
        return new MirrorBinaryTree.Node(node.value, copy(node.left), copy(node.right));
    }

    private static String serializeMirrorOracle(MirrorBinaryTree.Node node) {
        List<String> out = new ArrayList<>();
        serializeMirrorOracle(node, out);
        return String.join(",", out);
    }

    private static void serializeMirrorOracle(MirrorBinaryTree.Node node, List<String> out) {
        if (node == null) {
            out.add("#");
            return;
        }
        out.add(Integer.toString(node.value));
        serializeMirrorOracle(node.right, out);
        serializeMirrorOracle(node.left, out);
    }

    private static String serialize(MirrorBinaryTree.Node node) {
        List<String> out = new ArrayList<>();
        serialize(node, out);
        return String.join(",", out);
    }

    private static void serialize(MirrorBinaryTree.Node node, List<String> out) {
        if (node == null) {
            out.add("#");
            return;
        }
        out.add(Integer.toString(node.value));
        serialize(node.left, out);
        serialize(node.right, out);
    }

    private static void assertEquals(String expected, String actual, String label) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    private static void assertTrue(boolean condition, String label) {
        if (!condition) {
            throw new AssertionError(label);
        }
    }
}
