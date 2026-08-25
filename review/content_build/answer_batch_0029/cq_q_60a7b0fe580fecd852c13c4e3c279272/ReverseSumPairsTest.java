final class ReverseSumPairsTest {
    private static void expect(long expected, int[] nums) {
        long actual = ReverseSumPairs.countPairs(nums);
        if (actual != expected) {
            throw new AssertionError("expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        expect(0, new int[]{});
        expect(0, new int[]{1});
        expect(1, new int[]{12, 21});
        expect(3, new int[]{12, 21, 30});
        expect(6, new int[]{0, 0, 0, 0});
        expect(2, new int[]{12, 21, 13, 31});
        if (ReverseSumPairs.reverseNonNegativeInt(120) != 21L) throw new AssertionError("120 must reverse to 21");
        if (ReverseSumPairs.reverseNonNegativeInt(Integer.MAX_VALUE) != 7463847412L) throw new AssertionError("int reverse must use long");
        boolean nullRejected=false;
        try { ReverseSumPairs.countPairs(null); } catch (IllegalArgumentException expected) { nullRejected=true; }
        if (!nullRejected) throw new AssertionError("null contract must be explicit");
        boolean negativeRejected=false;
        try { ReverseSumPairs.countPairs(new int[]{-12, 12}); } catch (IllegalArgumentException expected) { negativeRejected=true; }
        if (!negativeRejected) throw new AssertionError("negative contract must be explicit");
        System.out.println("PASS empty=0 singleton=0 pair=1 triple-same-key=3 four-zero=6 mixed=2 leading-zero=21 int-reverse-uses-long null=rejected negative=rejected");
    }
}
