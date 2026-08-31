import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class RemoveNthWriterTest {
    private static final Random RNG = new Random(0x62D0B70DL);

    static RemoveNthFromEnd.ListNode build(int[] values) {
        RemoveNthFromEnd.ListNode dummy = new RemoveNthFromEnd.ListNode(0), tail = dummy;
        for (int v : values) { tail.next = new RemoveNthFromEnd.ListNode(v); tail = tail.next; }
        return dummy.next;
    }
    static int[] values(RemoveNthFromEnd.ListNode head) {
        List<Integer> out = new ArrayList<>();
        for (RemoveNthFromEnd.ListNode p = head; p != null; p = p.next) out.add(p.val);
        int[] a = new int[out.size()]; for (int i=0;i<a.length;i++) a[i]=out.get(i); return a;
    }
    static int[] oracle(int[] input, int n) {
        int[] out = new int[input.length - 1];
        int remove = input.length - n;
        for (int i=0,j=0;i<input.length;i++) if (i != remove) out[j++] = input[i];
        return out;
    }
    static void eq(int[] expected, int[] actual, String label) {
        if (!Arrays.equals(expected, actual)) throw new AssertionError(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
    }
    static void fixed(int[] input, int n, int[] expected, String label) {
        eq(expected, values(RemoveNthFromEnd.removeNthFromEnd(build(input), n)), label);
    }
    public static void main(String[] args) {
        fixed(new int[]{1},1,new int[]{},"single");
        fixed(new int[]{1,2},1,new int[]{1},"tail-two");
        fixed(new int[]{1,2},2,new int[]{2},"head-two");
        fixed(new int[]{1,2,3,4,5},2,new int[]{1,2,3,5},"example");
        fixed(new int[]{1,2,3,4,5},5,new int[]{2,3,4,5},"delete-head");
        fixed(new int[]{1,2,3,4,5},1,new int[]{1,2,3,4},"delete-tail");
        fixed(new int[]{7,7,7},2,new int[]{7,7},"duplicates");
        fixed(new int[]{-1,0,1},2,new int[]{-1,1},"values-unrestricted");
        fixed(new int[]{9,8,7,6},3,new int[]{9,7,6},"middle");
        fixed(new int[]{42,5,42,5},4,new int[]{5,42,5},"head-duplicate");
        boolean bad0=false,badNeg=false,badLarge=false,badEmpty=false;
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1}),0); } catch (IllegalArgumentException e) { bad0=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1}),-1); } catch (IllegalArgumentException e) { badNeg=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1,2}),3); } catch (IllegalArgumentException e) { badLarge=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(null,1); } catch (IllegalArgumentException e) { badEmpty=true; }
        if (!bad0 || !badNeg || !badLarge || !badEmpty) throw new AssertionError("invalid n/list boundary missing");

        int cases=0;
        for (int t=0;t<30000;t++) {
            int len=1+RNG.nextInt(40), n=1+RNG.nextInt(len);
            int[] input=new int[len]; for(int i=0;i<len;i++) input[i]=RNG.nextInt(15)-7;
            eq(oracle(input,n), values(RemoveNthFromEnd.removeNthFromEnd(build(input),n)), "random-"+t);
            cases++;
        }
        if(cases!=30000) throw new AssertionError("case count");
        System.out.println("PASS fixed=10 random_cases=30000 oracle=array-delete invalid_n=pass head_delete=pass tail_delete=pass");
    }
}
