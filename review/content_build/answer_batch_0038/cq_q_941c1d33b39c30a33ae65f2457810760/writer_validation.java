import java.util.*;

public class writer_validation {
    static String longestPalindrome(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        if (s.length() < 2) return s;
        int bestStart = 0;
        int bestLen = 1;
        for (int center = 0; center < s.length(); center++) {
            int[] odd = expand(s, center, center);
            int oddLen = odd[1] - odd[0] + 1;
            if (oddLen > bestLen || (oddLen == bestLen && odd[0] < bestStart)) {
                bestStart = odd[0]; bestLen = oddLen;
            }
            int[] even = expand(s, center, center + 1);
            if (even[0] <= even[1]) {
                int evenLen = even[1] - even[0] + 1;
                if (evenLen > bestLen || (evenLen == bestLen && even[0] < bestStart)) {
                    bestStart = even[0]; bestLen = evenLen;
                }
            }
        }
        return s.substring(bestStart, bestStart + bestLen);
    }

    static int[] expand(String s, int left, int right) {
        while (left >= 0 && right < s.length() && s.charAt(left) == s.charAt(right)) {
            left--; right++;
        }
        return new int[]{left + 1, right - 1};
    }

    static String oracle(String s) {
        int bestStart = 0, bestLen = 0;
        for (int i = 0; i < s.length(); i++) {
            for (int j = i; j < s.length(); j++) {
                if (j - i + 1 < bestLen) continue;
                boolean pal = true;
                for (int l=i,r=j;l<r;l++,r--) if (s.charAt(l)!=s.charAt(r)) { pal=false; break; }
                int len=j-i+1;
                if (pal && (len>bestLen || (len==bestLen && i<bestStart))) { bestStart=i; bestLen=len; }
            }
        }
        return s.substring(bestStart,bestStart+bestLen);
    }

    static void check(String s) {
        String got = longestPalindrome(s), expected = oracle(s);
        if (!got.equals(expected)) throw new AssertionError("s="+s+" got="+got+" expected="+expected);
    }

    public static void main(String[] args) {
        boolean rejected=false; try { longestPalindrome(null); } catch (IllegalArgumentException e) { rejected=true; }
        if(!rejected) throw new AssertionError("null accepted");
        String[] cases={"","a","aa","ab","aba","abba","babad","cbbd","aaaaa","abcda","bananas","forgeeksskeegfor"};
        for(String s:cases) check(s);
        Random r=new Random(20260826L); int randomized=0;
        String alphabet="abcd";
        for(int t=0;t<10000;t++){
            int n=r.nextInt(31); StringBuilder b=new StringBuilder();
            for(int i=0;i<n;i++) b.append(alphabet.charAt(r.nextInt(alphabet.length())));
            check(b.toString()); randomized++;
        }
        System.out.println("PASS null=rejected deterministic="+cases.length+" randomized="+randomized+" oracle=bruteforce tie=earliest-start");
    }
}
