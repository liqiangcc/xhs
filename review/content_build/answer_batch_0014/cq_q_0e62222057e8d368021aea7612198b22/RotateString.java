import java.util.Objects;

public final class RotateString {
    private RotateString() {}

    public static boolean rotateString(String s, String goal) {
        Objects.requireNonNull(s, "s");
        Objects.requireNonNull(goal, "goal");

        if (s.length() != goal.length()) {
            return false;
        }
        if (s.isEmpty()) {
            return true;
        }
        return containsInDoubledByKmp(s, goal);
    }

    private static boolean containsInDoubledByKmp(String s, String pattern) {
        int[] lps = buildLps(pattern);
        int matched = 0;
        int doubledLength = s.length() * 2;

        for (int i = 0; i < doubledLength; i++) {
            char current = s.charAt(i % s.length());
            while (matched > 0 && current != pattern.charAt(matched)) {
                matched = lps[matched - 1];
            }
            if (current == pattern.charAt(matched)) {
                matched++;
                if (matched == pattern.length()) {
                    return true;
                }
            }
        }
        return false;
    }

    private static int[] buildLps(String pattern) {
        int[] lps = new int[pattern.length()];
        int prefix = 0;
        for (int i = 1; i < pattern.length(); ) {
            if (pattern.charAt(i) == pattern.charAt(prefix)) {
                lps[i++] = ++prefix;
            } else if (prefix > 0) {
                prefix = lps[prefix - 1];
            } else {
                lps[i++] = 0;
            }
        }
        return lps;
    }
}
