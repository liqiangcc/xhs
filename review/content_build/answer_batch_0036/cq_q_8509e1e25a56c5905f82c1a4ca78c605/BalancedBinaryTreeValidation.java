import java.util.*;

public final class BalancedBinaryTreeValidation {
    static final class TreeNode {
        final int value;
        TreeNode left;
        TreeNode right;
        TreeNode(int value) { this.value = value; }
    }

    static boolean candidate(TreeNode root) { return heightIfBalanced(root) >= 0; }
    static int heightIfBalanced(TreeNode node) {
        if (node == null) return 0;
        int left = heightIfBalanced(node.left);
        if (left < 0) return -1;
        int right = heightIfBalanced(node.right);
        if (right < 0) return -1;
        if (Math.abs(left - right) > 1) return -1;
        return Math.max(left, right) + 1;
    }

    static boolean oracle(TreeNode node) {
        if (node == null) return true;
        return Math.abs(height(node.left) - height(node.right)) <= 1
                && oracle(node.left) && oracle(node.right);
    }
    static int height(TreeNode node) {
        if (node == null) return 0;
        return 1 + Math.max(height(node.left), height(node.right));
    }

    static TreeNode chain(int n) {
        if (n == 0) return null;
        TreeNode root = new TreeNode(0), cur = root;
        for (int i = 1; i < n; i++) { cur.left = new TreeNode(i); cur = cur.left; }
        return root;
    }

    static TreeNode complete(int n) {
        if (n == 0) return null;
        TreeNode[] nodes = new TreeNode[n];
        for (int i = 0; i < n; i++) nodes[i] = new TreeNode(i);
        for (int i = 0; i < n; i++) {
            int l = 2*i+1, r=2*i+2;
            if (l<n) nodes[i].left=nodes[l];
            if (r<n) nodes[i].right=nodes[r];
        }
        return nodes[0];
    }

    static TreeNode randomTree(Random r, int n) {
        if (n == 0) return null;
        TreeNode root = new TreeNode(0);
        List<TreeNode> available = new ArrayList<>();
        available.add(root);
        for (int value = 1; value < n; value++) {
            while (true) {
                TreeNode p = available.get(r.nextInt(available.size()));
                boolean leftFirst = r.nextBoolean();
                if (leftFirst && p.left == null) { p.left = new TreeNode(value); available.add(p.left); break; }
                if (!leftFirst && p.right == null) { p.right = new TreeNode(value); available.add(p.right); break; }
                if (p.left == null) { p.left = new TreeNode(value); available.add(p.left); break; }
                if (p.right == null) { p.right = new TreeNode(value); available.add(p.right); break; }
                available.remove(p);
            }
        }
        return root;
    }

    static void check(TreeNode root) {
        boolean a = candidate(root), b = oracle(root);
        if (a != b) throw new AssertionError("candidate=" + a + " oracle=" + b + " height=" + height(root));
    }

    public static void main(String[] args) {
        check(null);
        check(new TreeNode(1));
        check(complete(2));
        check(complete(3));
        check(complete(15));
        if (candidate(chain(3))) throw new AssertionError("3-node chain should be unbalanced");
        if (!candidate(chain(2))) throw new AssertionError("2-node chain should be balanced");

        TreeNode internal = new TreeNode(0);
        internal.left = new TreeNode(1);
        internal.right = new TreeNode(2);
        internal.left.left = new TreeNode(3);
        internal.left.left.left = new TreeNode(4);
        internal.right.right = new TreeNode(5);
        internal.right.right.right = new TreeNode(6);
        if (candidate(internal)) throw new AssertionError("internal imbalance must not be masked by root height equality");

        Random random = new Random(20260826L);
        int balanced = 0, unbalanced = 0;
        for (int i = 0; i < 5000; i++) {
            TreeNode root = randomTree(random, random.nextInt(31));
            check(root);
            if (oracle(root)) balanced++; else unbalanced++;
        }
        if (balanced == 0 || unbalanced == 0) throw new AssertionError("random corpus lacks both classes");
        System.out.println("PASS fixed=8 randomized=5000 oracle=independent-recomputed-height balanced="+balanced+" unbalanced="+unbalanced+" empty=true internal-imbalance=true linear-sentinel=true");
    }
}
