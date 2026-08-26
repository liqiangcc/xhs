import java.util.*;

class writer_validation {
    static int solve(String s) {
        if (s == null || s.isEmpty()) return 0;
        Map<Character, Integer> lastSeen = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            Integer previous = lastSeen.get(c);
            if (previous != null) left = Math.max(left, previous + 1);
            lastSeen.put(c, right);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    static int brute(String s) {
        if (s == null || s.isEmpty()) return 0;
        int best=0;
        for(int i=0;i<s.length();i++) {
            boolean[] seen=new boolean[1<<16];
            for(int j=i;j<s.length();j++) {
                char c=s.charAt(j);
                if(seen[c]) break;
                seen[c]=true;
                best=Math.max(best,j-i+1);
            }
        }
        return best;
    }

    static void enumerate(char[] a,int i,char[] alphabet,long[] count) {
        if(i==a.length) {
            String s=new String(a);
            int got=solve(s), expected=brute(s);
            if(got!=expected) throw new AssertionError("mismatch s="+s+" got="+got+" expected="+expected);
            count[0]++;
            return;
        }
        for(char c:alphabet){a[i]=c;enumerate(a,i+1,alphabet,count);}
    }

    public static void main(String[] args) {
        if(solve(null)!=0)throw new AssertionError("null");
        if(solve("")!=0)throw new AssertionError("empty");
        if(solve("abcabcbb")!=3)throw new AssertionError("classic");
        if(solve("bbbbb")!=1)throw new AssertionError("repeat");
        if(solve("pwwkew")!=3)throw new AssertionError("window");
        if(solve("abba")!=2)throw new AssertionError("left-backtrack");
        if(solve("dvdf")!=3)throw new AssertionError("history");

        char[] alphabet={'a','b','c','中'};
        long[] exhaustive={0};
        for(int n=0;n<=8;n++)enumerate(new char[n],0,alphabet,exhaustive);

        Random rnd=new Random(0x9a62670fL);
        char[] pool={'a','b','c','d','e','中','文','\u0000','\uD83D','\uDE00'};
        int randomized=10000;
        for(int t=0;t<randomized;t++){
            int n=rnd.nextInt(50);
            char[] a=new char[n];
            for(int i=0;i<n;i++)a[i]=pool[rnd.nextInt(pool.length)];
            String s=new String(a);
            int got=solve(s),expected=brute(s);
            if(got!=expected)throw new AssertionError("random mismatch got="+got+" expected="+expected+" length="+n);
        }
        System.out.println("PASS deterministic=7 exhaustive="+exhaustive[0]+" randomized="+randomized+" oracle=bruteforce-char-substrings contract=utf16-code-unit");
    }
}
