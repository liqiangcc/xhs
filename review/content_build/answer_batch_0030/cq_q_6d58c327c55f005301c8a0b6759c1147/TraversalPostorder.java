import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public final class TraversalPostorder {
    public static int[] toPostorder(int[] preorder, int[] inorder) {
        if (preorder == null || inorder == null || preorder.length != inorder.length) {
            throw new IllegalArgumentException("length mismatch");
        }
        int n = preorder.length;
        Map<Integer,Integer> inIndex = new HashMap<>();
        for (int i=0;i<n;i++) {
            if (inIndex.put(inorder[i], i) != null) throw new IllegalArgumentException("duplicate node value");
        }
        Set<Integer> seenPre = new HashSet<>();
        for (int value : preorder) {
            if (!seenPre.add(value) || !inIndex.containsKey(value)) throw new IllegalArgumentException("invalid traversal set");
        }
        int[] out = new int[n];
        int[] write = {0};
        emit(preorder, 0, 0, n, inIndex, out, write);
        if (write[0] != n) throw new IllegalArgumentException("inconsistent traversal length");
        return out;
    }
    private static void emit(int[] pre, int preL, int inL, int len, Map<Integer,Integer> inIndex, int[] out, int[] write) {
        if (len == 0) return;
        if (preL < 0 || preL >= pre.length || preL + len > pre.length) throw new IllegalArgumentException("preorder interval invalid");
        int root = pre[preL];
        Integer rootIndex = inIndex.get(root);
        if (rootIndex == null || rootIndex < inL || rootIndex >= inL + len) throw new IllegalArgumentException("inconsistent traversals");
        int leftSize = rootIndex - inL;
        int rightSize = len - 1 - leftSize;
        emit(pre, preL + 1, inL, leftSize, inIndex, out, write);
        emit(pre, preL + 1 + leftSize, rootIndex + 1, rightSize, inIndex, out, write);
        out[write[0]++] = root;
    }
}
