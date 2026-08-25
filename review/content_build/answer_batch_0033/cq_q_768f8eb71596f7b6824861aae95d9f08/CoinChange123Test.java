import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class CoinChange123Test {
    private static Set<String> oracle(int n) {
        Set<String> out = new HashSet<>();
        if (n < 0) return out;
        for (int three = 0; 3 * three <= n; three++) {
            for (int two = 0; 3 * three + 2 * two <= n; two++) {
                int one = n - 3 * three - 2 * two;
                out.add(one + "," + two + "," + three);
            }
        }
        return out;
    }

    private static Set<String> actual(int n) {
        List<CoinChange123.Combination> rows = CoinChange123.combinations(n);
        Set<String> seen = new HashSet<>();
        for (CoinChange123.Combination c : rows) {
            if (c.oneCent() < 0 || c.twoCent() < 0 || c.threeCent() < 0) {
                throw new AssertionError("negative coin count");
            }
            if (c.oneCent() + 2 * c.twoCent() + 3 * c.threeCent() != n) {
                throw new AssertionError("sum mismatch for n=" + n + ": " + c);
            }
            String key = c.oneCent() + "," + c.twoCent() + "," + c.threeCent();
            if (!seen.add(key)) throw new AssertionError("duplicate combination: " + key);
        }
        if (seen.size() != rows.size()) throw new AssertionError("duplicate rows");
        return seen;
    }

    private static void check(int n) {
        Set<String> expected = oracle(n);
        Set<String> got = actual(n);
        if (!got.equals(expected)) {
            throw new AssertionError("enumeration mismatch n=" + n + " expected=" + expected + " got=" + got);
        }
        long dp = CoinChange123.countWaysDp(n);
        if (dp != expected.size()) {
            throw new AssertionError("DP count mismatch n=" + n + " expected=" + expected.size() + " got=" + dp);
        }
    }

    public static void main(String[] args) {
        if (!CoinChange123.combinations(-1).isEmpty()) throw new AssertionError("negative enumeration must be empty");
        if (CoinChange123.countWaysDp(-1) != 0L) throw new AssertionError("negative DP count must be zero");
        check(0);
        check(1);
        check(2);
        check(3);
        check(4);
        check(5);
        for (int n = 0; n <= 200; n++) check(n);
        if (CoinChange123.countWaysDp(4) != 4L) throw new AssertionError("n=4 known count");
        System.out.println("PASS fixed=0..5 exhaustive=0..200 enumeration=unique-complete dp=count negative=empty");
    }
}
