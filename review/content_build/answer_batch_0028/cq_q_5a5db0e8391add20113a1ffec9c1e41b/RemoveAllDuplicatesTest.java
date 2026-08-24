public final class RemoveAllDuplicatesTest {
    public static void main(String[] args) {
        check(new int[]{}, new int[]{});
        check(new int[]{1}, new int[]{1});
        check(new int[]{1,2,3}, new int[]{1,2,3});
        check(new int[]{1,1}, new int[]{});
        check(new int[]{1,1,2,3}, new int[]{2,3});
        check(new int[]{1,2,2,3}, new int[]{1,3});
        check(new int[]{1,2,3,3}, new int[]{1,2});
        check(new int[]{1,1,2,2,3,3}, new int[]{});
        check(new int[]{1,2,3,3,4,4,5}, new int[]{1,2,5});
        check(new int[]{1,1,1,2,3,4,4,5,5,6}, new int[]{2,3,6});
        System.out.println("PASS cases=10 sample=1->2->5 head-middle-tail-all-duplicates-covered");
    }

    private static void check(int[] input, int[] expected) {
        RemoveAllDuplicates.ListNode dummy = new RemoveAllDuplicates.ListNode(0), tail = dummy;
        for (int v : input) {
            tail.next = new RemoveAllDuplicates.ListNode(v);
            tail = tail.next;
        }
        RemoveAllDuplicates.ListNode out = RemoveAllDuplicates.deleteDuplicates(dummy.next);
        int i = 0;
        while (out != null) {
            if (i >= expected.length || out.val != expected[i]) throw new AssertionError("mismatch at " + i);
            i++;
            out = out.next;
        }
        if (i != expected.length) throw new AssertionError("length mismatch expected=" + expected.length + " actual=" + i);
    }

    private RemoveAllDuplicatesTest() {}
}
