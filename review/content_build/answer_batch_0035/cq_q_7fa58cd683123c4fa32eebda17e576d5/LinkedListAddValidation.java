import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class LinkedListAddValidation {
    static final class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    static ListNode addTwoNumbers(ListNode l1, ListNode l2) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        int carry = 0;
        while (l1 != null || l2 != null || carry != 0) {
            int a = l1 == null ? 0 : l1.val;
            int b = l2 == null ? 0 : l2.val;
            int sum = a + b + carry;
            tail.next = new ListNode(sum % 10);
            tail = tail.next;
            carry = sum / 10;
            if (l1 != null) l1 = l1.next;
            if (l2 != null) l2 = l2.next;
        }
        return dummy.next;
    }

    static ListNode of(int... digits) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        for (int d : digits) {
            if (d < 0 || d > 9) throw new IllegalArgumentException("digit out of range: " + d);
            tail.next = new ListNode(d);
            tail = tail.next;
        }
        return dummy.next;
    }

    static List<Integer> digits(ListNode node) {
        List<Integer> out = new ArrayList<>();
        while (node != null) {
            out.add(node.val);
            node = node.next;
        }
        return out;
    }

    static void expect(int[] left, int[] right, Integer... expected) {
        ListNode l1 = of(left);
        ListNode l2 = of(right);
        List<Integer> actual = digits(addTwoNumbers(l1, l2));
        if (!actual.equals(Arrays.asList(expected))) {
            throw new AssertionError("left=" + Arrays.toString(left)
                    + " right=" + Arrays.toString(right)
                    + " expected=" + Arrays.asList(expected)
                    + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        expect(new int[]{2,4,3}, new int[]{5,6,4}, 7,0,8);   // 342 + 465 = 807
        expect(new int[]{0}, new int[]{0}, 0);               // zero
        expect(new int[]{9,9}, new int[]{1}, 0,0,1);         // final carry
        expect(new int[]{1}, new int[]{9,9,9}, 0,0,0,1);     // unequal lengths + carry chain
        expect(new int[]{5}, new int[]{5}, 0,1);             // one digit carry
        expect(new int[]{9,1}, new int[]{1,8}, 0,0,1);       // 19 + 81 = 100
        System.out.println("PASS examples=6 reverse-order=true unequal-length=true carry-chain=true final-carry=true zero=true");
    }
}
