final class HouseRobberTest {
    private static void expect(long expected, int[] nums) {
        long actual = HouseRobber.rob(nums);
        if (actual != expected) {
            throw new AssertionError("expected=" + expected + " actual=" + actual);
        }
    }
    public static void main(String[] args) {
        expect(0, new int[]{});
        expect(5, new int[]{5});
        expect(2, new int[]{2, 1});
        expect(4, new int[]{1, 2, 3, 1});
        expect(12, new int[]{2, 7, 9, 3, 1});
        expect(4, new int[]{2, 1, 1, 2});
        expect(0, new int[]{0, 0, 0, 0});
        boolean rejected = false;
        try { HouseRobber.rob(null); } catch (IllegalArgumentException expected) { rejected = true; }
        if (!rejected) throw new AssertionError("null contract must be explicit and rejected");
        System.out.println("PASS empty=0 single=5 canonical-example=4 second-example=12 greedy-counterexample=4 zeros=0 null=rejected");
    }
}
