public final class ExpressionEvaluatorTest {
    private static void eq(long expected, String expression) {
        long actual = ExpressionEvaluator.evaluate(expression);
        if (actual != expected) throw new AssertionError(expression + ": expected=" + expected + " actual=" + actual);
    }

    private static void fails(String expression, Class<? extends Throwable> type) {
        try {
            ExpressionEvaluator.evaluate(expression);
            throw new AssertionError("expected failure: " + expression);
        } catch (Throwable t) {
            if (!type.isInstance(t)) throw new AssertionError("wrong failure for " + expression + ": " + t, t);
        }
    }

    public static void main(String[] args) {
        eq(14, "2 + 3 * 4");
        eq(20, "(2 + 3) * 4");
        eq(46, "2 * (3 + (4 * 5))");
        eq(-20, "-(2 + 3) * 4");
        eq(3, "1--2");
        eq(3, "8-3-2");
        eq(1, "8/4/2");
        eq(3, "7/2");
        eq(-3, "-7/2");
        fails("", IllegalArgumentException.class);
        fails("1+", IllegalArgumentException.class);
        fails("(1+2", IllegalArgumentException.class);
        fails("1 2", IllegalArgumentException.class);
        fails("1+2x", IllegalArgumentException.class);
        fails("1/0", ArithmeticException.class);
        fails("9223372036854775807+1", ArithmeticException.class);
        System.out.println("PASS precedence parentheses nesting unary left-associativity division invalid-input divide-zero overflow");
    }
}
