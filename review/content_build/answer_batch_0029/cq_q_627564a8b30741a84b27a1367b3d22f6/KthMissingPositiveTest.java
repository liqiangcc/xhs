final class KthMissingPositiveTest {
    private static void expect(long expected, int[] arr, long k) {
        long actual = KthMissingPositive.kthMissing(arr, k);
        if (actual != expected) throw new AssertionError("expected=" + expected + " actual=" + actual);
    }
    public static void main(String[] args) {
        expect(9, new int[]{2,3,4,7,11}, 5);
        expect(6, new int[]{1,2,3,4}, 2);
        expect(1, new int[]{2}, 1);
        expect(5, new int[]{}, 5);
        expect(8, new int[]{1,3,5,7}, 4);
        expect(3_000_000_000L, new int[]{1}, 2_999_999_999L);
        boolean nullRejected=false;
        try { KthMissingPositive.kthMissing(null, 1); } catch (IllegalArgumentException expected) { nullRejected=true; }
        if (!nullRejected) throw new AssertionError("null must be rejected");
        boolean kRejected=false;
        try { KthMissingPositive.kthMissing(new int[]{1,2}, 0); } catch (IllegalArgumentException expected) { kRejected=true; }
        if (!kRejected) throw new AssertionError("k<=0 must be rejected");
        System.out.println("PASS canonical=9 tail=6 before-first=1 empty=5 gaps=8 long-result=3000000000 null=rejected nonpositive-k=rejected");
    }
}
