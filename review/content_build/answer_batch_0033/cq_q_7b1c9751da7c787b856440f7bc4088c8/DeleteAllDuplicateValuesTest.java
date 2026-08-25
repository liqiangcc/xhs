import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public final class DeleteAllDuplicateValuesTest {
    static DeleteAllDuplicateValues.ListNode list(int... values) {
        DeleteAllDuplicateValues.ListNode dummy = new DeleteAllDuplicateValues.ListNode(0), tail = dummy;
        for (int v : values) { tail.next = new DeleteAllDuplicateValues.ListNode(v); tail = tail.next; }
        return dummy.next;
    }
    static int[] array(DeleteAllDuplicateValues.ListNode head) {
        List<Integer> out = new ArrayList<>();
        for (var p = head; p != null; p = p.next) out.add(p.val);
        return out.stream().mapToInt(Integer::intValue).toArray();
    }
    static int[] oracle(int[] input) {
        Map<Integer,Integer> counts = new TreeMap<>();
        for (int v : input) counts.merge(v, 1, Integer::sum);
        return Arrays.stream(input).filter(v -> counts.get(v) == 1).toArray();
    }
    static void check(int[] in, int[] expected) {
        int[] actual = array(DeleteAllDuplicateValues.deleteAllDuplicates(list(in)));
        if (!Arrays.equals(actual, expected)) throw new AssertionError(Arrays.toString(in)+" -> "+Arrays.toString(actual)+" expected "+Arrays.toString(expected));
    }
    public static void main(String[] args) {
        check(new int[]{}, new int[]{});
        check(new int[]{1}, new int[]{1});
        check(new int[]{1,2,3}, new int[]{1,2,3});
        check(new int[]{1,1}, new int[]{});
        check(new int[]{1,2,1,3}, new int[]{2,3});
        check(new int[]{1,2,2,3,3,4}, new int[]{1,4});
        check(new int[]{1,2,3,2,4,1,5,5,6}, new int[]{3,4,6});
        int exhaustive = 0;
        for (int len = 0; len <= 7; len++) {
            int total = 1;
            for (int i=0;i<len;i++) total *= 4;
            for (int mask=0; mask<total; mask++) {
                int[] in = new int[len]; int x=mask;
                for (int i=0;i<len;i++) { in[i]=x%4; x/=4; }
                check(in, oracle(in)); exhaustive++;
            }
        }
        System.out.println("PASS fixed=7 exhaustive="+exhaustive+" unsorted=true no-map-set-in-solution=true");
    }
}
