public final class ExpressionEvaluator {
    private final String input;
    private int pos;

    private ExpressionEvaluator(String input) {
        this.input = input;
    }

    public static long evaluate(String expression) {
        if (expression == null) throw new IllegalArgumentException("expression is null");
        ExpressionEvaluator p = new ExpressionEvaluator(expression);
        long value = p.parseExpression();
        p.skipWhitespace();
        if (p.pos != p.input.length()) {
            throw new IllegalArgumentException("unexpected token at position " + p.pos);
        }
        return value;
    }

    private long parseExpression() {
        long value = parseTerm();
        while (true) {
            if (consume('+')) value = Math.addExact(value, parseTerm());
            else if (consume('-')) value = Math.subtractExact(value, parseTerm());
            else return value;
        }
    }

    private long parseTerm() {
        long value = parseUnary();
        while (true) {
            if (consume('*')) value = Math.multiplyExact(value, parseUnary());
            else if (consume('/')) value = Math.divideExact(value, parseUnary());
            else return value;
        }
    }

    private long parseUnary() {
        if (consume('+')) return parseUnary();
        if (consume('-')) return Math.negateExact(parseUnary());
        return parsePrimary();
    }

    private long parsePrimary() {
        skipWhitespace();
        if (consume('(')) {
            long value = parseExpression();
            if (!consume(')')) throw new IllegalArgumentException("missing ')' at position " + pos);
            return value;
        }
        return parseNumber();
    }

    private long parseNumber() {
        skipWhitespace();
        int start = pos;
        long value = 0;
        while (pos < input.length() && input.charAt(pos) >= '0' && input.charAt(pos) <= '9') {
            int digit = input.charAt(pos++) - '0';
            value = Math.addExact(Math.multiplyExact(value, 10L), digit);
        }
        if (pos == start) throw new IllegalArgumentException("number expected at position " + pos);
        return value;
    }

    private boolean consume(char expected) {
        skipWhitespace();
        if (pos < input.length() && input.charAt(pos) == expected) {
            pos++;
            return true;
        }
        return false;
    }

    private void skipWhitespace() {
        while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) pos++;
    }
}
