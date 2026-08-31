import java.util.Random;

public final class LongestValidParenthesesReviewerTest {
  private static final Random RNG = new Random(0x62006C5AL ^ 0x51A7E2L);
  private static int oracle(String s) {
    int best = 0;
    for (int start = 0; start < s.length(); start++) {
      int balance = 0;
      for (int end = start; end < s.length(); end++) {
        char ch = s.charAt(end);
        if (ch == '(') balance++;
        else if (ch == ')') balance--;
        else throw new IllegalArgumentException("oracle expects parentheses only");
        if (balance < 0) break;
        if (balance == 0) best = Math.max(best, end - start + 1);
      }
    }
    return best;
  }
  private static void check(String s, int expected, String label) {
    int actual = LongestValidParentheses.longestValidParentheses(s);
    if (actual != expected) throw new AssertionError(label + " expected=" + expected + " actual=" + actual + " s=" + s);
  }
  private static String fromMask(int len, int mask) {
    StringBuilder sb = new StringBuilder(len);
    for (int i = 0; i < len; i++) sb.append(((mask >>> i) & 1) == 0 ? '(' : ')');
    return sb.toString();
  }
  private static String randomString(int maxLen) {
    int len = RNG.nextInt(maxLen + 1);
    StringBuilder sb = new StringBuilder(len);
    for (int i = 0; i < len; i++) sb.append(RNG.nextBoolean() ? '(' : ')');
    return sb.toString();
  }
  public static void main(String[] args) {
    String[] fixed = {"", "(", ")", "()", "(()", ")()())", "()(())", "((()))", "()(()", "())()", "(()())", "())(())", "()()()", "((())())"};
    for (int i = 0; i < fixed.length; i++) check(fixed[i], oracle(fixed[i]), "fixed-" + i);
    int exhaustive = 0;
    for (int len = 0; len <= 12; len++) {
      int count = 1 << len;
      for (int mask = 0; mask < count; mask++) {
        String s = fromMask(len, mask);
        check(s, oracle(s), "exhaustive-" + exhaustive);
        exhaustive++;
      }
    }
    if (exhaustive != 8191) throw new AssertionError("unexpected exhaustive count=" + exhaustive);
    for (int i = 0; i < 20000; i++) {
      String s = randomString(50);
      check(s, oracle(s), "random-" + i);
    }
    boolean nullThrew = false, invalidThrew = false;
    try { LongestValidParentheses.longestValidParentheses(null); } catch (IllegalArgumentException expected) { nullThrew = true; }
    try { LongestValidParentheses.longestValidParentheses("()a()"); } catch (IllegalArgumentException expected) { invalidThrew = true; }
    if (!nullThrew || !invalidThrew) throw new AssertionError("declared input contract not enforced");
    System.out.println("PASS reviewer fixed=14 exhaustive=8191 random=20000 oracle=quadratic-balance-scan null=throws invalid=throws");
  }
}
