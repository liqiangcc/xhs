final class RootToLeafNumberSumTest {
    static RootToLeafNumberSum.TreeNode n(int v) { return new RootToLeafNumberSum.TreeNode(v); }
    static void eq(long expected, long actual, String name) {
        if (expected != actual) throw new AssertionError(name + ": expected=" + expected + " actual=" + actual);
    }
    public static void main(String[] args) {
        eq(0L, RootToLeafNumberSum.sumRootToLeafNumbers(null), "empty");
        eq(5L, RootToLeafNumberSum.sumRootToLeafNumbers(n(5)), "single");

        var r = n(1); r.left = n(2); r.right = n(3);
        eq(25L, RootToLeafNumberSum.sumRootToLeafNumbers(r), "two leaves");

        var z = n(0); z.left = n(1); z.left.right = n(3); z.right = n(2);
        eq(15L, RootToLeafNumberSum.sumRootToLeafNumbers(z), "leading zero asymmetric");

        var c = n(4); c.left = n(9); c.right = n(0); c.left.left = n(5); c.left.right = n(1);
        eq(1026L, RootToLeafNumberSum.sumRootToLeafNumbers(c), "multiple leaves");

        boolean bad = false;
        try { RootToLeafNumberSum.sumRootToLeafNumbers(n(10)); }
        catch (IllegalArgumentException expected) { bad = true; }
        if (!bad) throw new AssertionError("non-digit must fail closed");

        var deep = n(9); var p = deep;
        for (int i = 1; i < 19; i++) { p.left = n(9); p = p.left; }
        boolean overflow = false;
        try { RootToLeafNumberSum.sumRootToLeafNumbers(deep); }
        catch (ArithmeticException expected) { overflow = true; }
        if (!overflow) throw new AssertionError("overflow must be explicit");

        System.out.println("PASS empty single two-leaves asymmetric-leading-zero multiple-leaves non-digit-rejected overflow-explicit");
    }
}
