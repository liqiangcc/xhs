import java.util.*;

public final class MergeTwoSortedListsTest {
    private static MergeTwoSortedLists.ListNode list(int... xs) {
        MergeTwoSortedLists.ListNode d = new MergeTwoSortedLists.ListNode(0), t = d;
        for (int x : xs) { t.next = new MergeTwoSortedLists.ListNode(x); t = t.next; }
        return d.next;
    }
    private static int[] vals(MergeTwoSortedLists.ListNode h) {
        ArrayList<Integer> a = new ArrayList<>();
        int guard = 0;
        while (h != null) { if (++guard > 10000) throw new AssertionError("cycle"); a.add(h.val); h = h.next; }
        return a.stream().mapToInt(Integer::intValue).toArray();
    }
    private static void eq(int[] got, int[] want, String label) {
        if (!Arrays.equals(got, want)) throw new AssertionError(label + " got=" + Arrays.toString(got));
    }
    private static int[] oracle(int[] a, int[] b) {
        int[] out = new int[a.length + b.length]; int i=0,j=0,k=0;
        while (i<a.length && j<b.length) out[k++] = a[i] <= b[j] ? a[i++] : b[j++];
        while (i<a.length) out[k++] = a[i++]; while (j<b.length) out[k++] = b[j++];
        return out;
    }
    public static void main(String[] args) {
        eq(vals(MergeTwoSortedLists.merge(list(1,2,4), list(1,3,4))), new int[]{1,1,2,3,4,4}, "canonical");
        eq(vals(MergeTwoSortedLists.merge(null, list(1,2))), new int[]{1,2}, "left-empty");
        eq(vals(MergeTwoSortedLists.merge(list(-3,-1,5), null)), new int[]{-3,-1,5}, "right-empty");
        eq(vals(MergeTwoSortedLists.merge(null, null)), new int[]{}, "both-empty");
        eq(vals(MergeTwoSortedLists.merge(list(1,1,1), list(1,1))), new int[]{1,1,1,1,1}, "duplicates");
        MergeTwoSortedLists.ListNode a1 = new MergeTwoSortedLists.ListNode(1);
        MergeTwoSortedLists.ListNode a2 = new MergeTwoSortedLists.ListNode(3); a1.next = a2;
        MergeTwoSortedLists.ListNode b1 = new MergeTwoSortedLists.ListNode(2);
        MergeTwoSortedLists.ListNode b2 = new MergeTwoSortedLists.ListNode(4); b1.next = b2;
        MergeTwoSortedLists.ListNode merged = MergeTwoSortedLists.merge(a1, b1);
        if (merged != a1 || merged.next != b1 || merged.next.next != a2 || merged.next.next.next != b2) throw new AssertionError("must reuse original nodes");
        Random r = new Random(20260830L);
        for (int c=0;c<5000;c++) {
            int n=r.nextInt(25), m=r.nextInt(25); int[] x=new int[n], y=new int[m];
            for(int i=0;i<n;i++) x[i]=r.nextInt(41)-20; for(int i=0;i<m;i++) y[i]=r.nextInt(41)-20;
            Arrays.sort(x); Arrays.sort(y); eq(vals(MergeTwoSortedLists.merge(list(x),list(y))),oracle(x,y),"random-"+c);
        }
        System.out.println("PASS fixed=6 randomized=5000 oracle=two-pointer node-reuse=true empty=true duplicates=true negatives=true");
    }
}
