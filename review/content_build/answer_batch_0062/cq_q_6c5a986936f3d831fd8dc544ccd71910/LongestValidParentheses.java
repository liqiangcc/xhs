import java.util.ArrayDeque;
import java.util.Deque;

public final class LongestValidParentheses {
    private LongestValidParentheses() {}

    public static int longestValidParentheses(String s) {
        if (s == null) throw new IllegalArgumentException("input must be non-null");
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(-1);
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '(') {
                stack.push(i);
            } else if (ch == ')') {
                stack.pop();
                if (stack.isEmpty()) stack.push(i);
                else best = Math.max(best, i - stack.peek());
            } else {
                throw new IllegalArgumentException("only '(' and ')' are allowed");
            }
        }
        return best;
    }
}
