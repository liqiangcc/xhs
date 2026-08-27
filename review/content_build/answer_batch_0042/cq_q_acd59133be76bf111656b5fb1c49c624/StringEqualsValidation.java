import java.util.HashMap;
import java.util.HashSet;

public final class StringEqualsValidation {
    private static int cases = 0;

    private static void expect(boolean condition, String message) {
        cases++;
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        char[] raw = {'a','b','c'};
        Solution.MyString a = new Solution.MyString(raw);
        Solution.MyString b = new Solution.MyString(new char[]{'a','b','c'});
        Solution.MyString c = new Solution.MyString(new char[]{'a','b','c'});
        Solution.MyString diffLast = new Solution.MyString(new char[]{'a','b','d'});
        Solution.MyString shorter = new Solution.MyString(new char[]{'a','b'});
        Solution.MyString empty1 = new Solution.MyString(new char[]{});
        Solution.MyString empty2 = new Solution.MyString(new char[]{});
        Solution.MyString unicode1 = new Solution.MyString(new char[]{'中','文','\uD83D','\uDE00'});
        Solution.MyString unicode2 = new Solution.MyString(new char[]{'中','文','\uD83D','\uDE00'});

        expect(a.equals(a), "reflexive identity");
        expect(a.equals(b) && b.equals(a), "symmetric equal values");
        expect(a.equals(b) && b.equals(c) && a.equals(c), "transitive");
        expect(!a.equals(null), "null false");
        expect(!a.equals("abc"), "other type false");
        expect(!a.equals(shorter), "length mismatch");
        expect(!a.equals(diffLast), "content mismatch");
        expect(empty1.equals(empty2), "empty equal");
        expect(unicode1.equals(unicode2), "unicode char sequence equal");
        expect(a.hashCode() == b.hashCode(), "equal hash");
        expect(a.length() == 3, "length stable");

        raw[0] = 'z';
        expect(a.equals(b), "defensive copy protects value after caller mutation");
        expect(a.hashCode() == b.hashCode(), "defensive copy protects hash after caller mutation");

        HashSet<Solution.MyString> set = new HashSet<>();
        set.add(a);
        expect(set.contains(b), "hash set lookup by equal value");

        HashMap<Solution.MyString, Integer> map = new HashMap<>();
        map.put(a, 7);
        expect(map.get(b) == 7, "hash map lookup by equal value");

        for (int len = 0; len <= 6; len++) {
            int count = 1 << len;
            for (int bits = 0; bits < count; bits++) {
                char[] x = new char[len];
                for (int i = 0; i < len; i++) x[i] = ((bits >>> i) & 1) == 0 ? 'a' : 'b';
                Solution.MyString left = new Solution.MyString(x);
                Solution.MyString right = new Solution.MyString(x.clone());
                expect(left.equals(right), "generated equal sequence");
                expect(left.hashCode() == right.hashCode(), "generated hash contract");
                if (len > 0) {
                    char[] y = x.clone();
                    y[len - 1] = y[len - 1] == 'a' ? 'b' : 'a';
                    expect(!left.equals(new Solution.MyString(y)), "generated one-char mismatch");
                }
            }
        }

        boolean npe = false;
        try { new Solution.MyString(null); }
        catch (NullPointerException expected) { npe = true; }
        expect(npe, "null backing input rejected");

        System.out.println("PASS cases=" + cases + " reflexive+symmetric+transitive+null+type+length+content+unicode+hash+defensive-copy+collections=covered");
    }
}
