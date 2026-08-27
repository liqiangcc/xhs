public final class Solution {
    public String longestCommonPrefix(String[] strs) {
        if (strs == null) throw new IllegalArgumentException("strs must not be null");
        if (strs.length == 0) return "";
        for (String s : strs) if (s == null) throw new IllegalArgumentException("element must not be null");
        String first = strs[0];
        for (int i = 0; i < first.length(); i++) {
            char expected = first.charAt(i);
            for (int j = 1; j < strs.length; j++) {
                if (i >= strs[j].length() || strs[j].charAt(i) != expected) return first.substring(0, i);
            }
        }
        return first;
    }
}
