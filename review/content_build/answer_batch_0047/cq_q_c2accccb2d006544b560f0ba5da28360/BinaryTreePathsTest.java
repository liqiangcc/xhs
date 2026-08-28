import java.util.List;

public final class BinaryTreePathsTest {
    private static void assertEquals(Object expected, Object actual, String message) {
        if (!expected.equals(actual)) {
            throw new AssertionError(message + " expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        assertEquals(List.of(), BinaryTreePaths.allRootToLeafPaths(null), "null tree");

        BinaryTreePaths.TreeNode single = new BinaryTreePaths.TreeNode(7);
        assertEquals(List.of(List.of(7)), BinaryTreePaths.allRootToLeafPaths(single), "single node");

        BinaryTreePaths.TreeNode root = new BinaryTreePaths.TreeNode(1);
        root.left = new BinaryTreePaths.TreeNode(2);
        root.right = new BinaryTreePaths.TreeNode(3);
        root.left.right = new BinaryTreePaths.TreeNode(5);
        assertEquals(
                List.of(List.of(1, 2, 5), List.of(1, 3)),
                BinaryTreePaths.allRootToLeafPaths(root),
                "branching tree left-first contract");

        BinaryTreePaths.TreeNode chain = new BinaryTreePaths.TreeNode(4);
        chain.right = new BinaryTreePaths.TreeNode(5);
        chain.right.right = new BinaryTreePaths.TreeNode(6);
        assertEquals(List.of(List.of(4, 5, 6)), BinaryTreePaths.allRootToLeafPaths(chain), "one-child chain");

        BinaryTreePaths.TreeNode duplicates = new BinaryTreePaths.TreeNode(1);
        duplicates.left = new BinaryTreePaths.TreeNode(1);
        duplicates.right = new BinaryTreePaths.TreeNode(1);
        assertEquals(
                List.of(List.of(1, 1), List.of(1, 1)),
                BinaryTreePaths.allRootToLeafPaths(duplicates),
                "structurally distinct equal-valued paths are preserved");

        System.out.println("PASS null=empty single=one branching=left-first one-child=not-leaf duplicate-values=preserved");
    }
}
