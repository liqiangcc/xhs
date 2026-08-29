import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;

public final class UniqueBstsTest {
    private static Set<String> shapes(int nodes) {
        Set<String> out = new HashSet<>();
        if (nodes == 0) {
            out.add("#");
            return out;
        }
        for (int left = 0; left < nodes; left++) {
            int right = nodes - 1 - left;
            for (String l : shapes(left)) {
                for (String r : shapes(right)) {
                    out.add("(" + l + "," + r + ")");
                }
            }
        }
        return out;
    }

    private static BigInteger catalanClosedForm(int n) {
        BigInteger choose = BigInteger.ONE;
        for (int k = 1; k <= n; k++) {
            choose = choose.multiply(BigInteger.valueOf(n + k)).divide(BigInteger.valueOf(k));
        }
        return choose.divide(BigInteger.valueOf(n + 1L));
    }

    public static void main(String[] args) {
        for (int n = 0; n <= 8; n++) {
            BigInteger actual = UniqueBsts.countUniqueBsts(n);
            BigInteger oracle = BigInteger.valueOf(shapes(n).size());
            if (!actual.equals(oracle)) {
                throw new AssertionError("shape oracle mismatch n=" + n + " actual=" + actual + " oracle=" + oracle);
            }
        }
        for (int n = 0; n <= 50; n++) {
            BigInteger actual = UniqueBsts.countUniqueBsts(n);
            BigInteger oracle = catalanClosedForm(n);
            if (!actual.equals(oracle)) {
                throw new AssertionError("closed-form mismatch n=" + n + " actual=" + actual + " oracle=" + oracle);
            }
        }
        try {
            UniqueBsts.countUniqueBsts(-1);
            throw new AssertionError("negative n must fail");
        } catch (IllegalArgumentException expected) {
            // expected
        }
        BigInteger n100 = UniqueBsts.countUniqueBsts(100);
        if (!n100.toString().equals("896519947090131496687170070074100632420837521538745909320")) {
            throw new AssertionError("n=100 regression mismatch: " + n100);
        }
        System.out.println("PASS exhaustive-shapes=0..8 closed-form=0..50 negative=rejected n100=exact-bigint");
    }
}
