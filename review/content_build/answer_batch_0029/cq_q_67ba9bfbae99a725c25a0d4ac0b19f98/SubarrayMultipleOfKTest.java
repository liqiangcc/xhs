final class SubarrayMultipleOfKTest {
    private static void expectCount(long expected, int[] nums, int k) {
        long actual = SubarrayMultipleOfK.countSubarraysMultipleOfK(nums, k);
        if (actual != expected) throw new AssertionError("count expected=" + expected + " actual=" + actual);
    }
    private static void expectExists(boolean expected, int[] nums, int k) {
        boolean actual = SubarrayMultipleOfK.existsLengthAtLeastTwoMultipleOfK(nums, k);
        if (actual != expected) throw new AssertionError("exists expected=" + expected + " actual=" + actual);
    }
    public static void main(String[] args) {
        expectCount(7, new int[]{4,5,0,-2,-3,1}, 5);
        expectCount(6, new int[]{0,0,0}, 5);
        expectCount(3, new int[]{-1,1,-4,4}, 5);
        expectCount(7, new int[]{4,5,0,-2,-3,1}, -5);
        expectExists(true, new int[]{23,2,4,6,7}, 6);
        expectExists(true, new int[]{23,2,6,4,7}, 6);
        expectExists(false, new int[]{23,2,6,4,7}, 13);
        expectExists(true, new int[]{0,0}, 7);
        boolean zeroRejected=false;
        try { SubarrayMultipleOfK.countSubarraysMultipleOfK(new int[]{0}, 0); } catch (IllegalArgumentException expected) { zeroRejected=true; }
        if (!zeroRejected) throw new AssertionError("k=0 must be explicit");
        boolean nullRejected=false;
        try { SubarrayMultipleOfK.existsLengthAtLeastTwoMultipleOfK(null, 5); } catch (IllegalArgumentException expected) { nullRejected=true; }
        if (!nullRejected) throw new AssertionError("null must be rejected");
        System.out.println("PASS count-standard=7 count-zeros=6 count-negative-elements=3 negative-k=7 exists-standard=true exists-alt=true exists-false=false length-two-zero=true k-zero=rejected null=rejected");
    }
}
