import java.util.Arrays;
import java.util.List;

public final class PrimeRangeTest {
    private static boolean oracle(int n) {
        if (n < 2) return false;
        for (int d = 2; d < n; d++) {
            if (n % d == 0) return false;
        }
        return true;
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        List<Integer> expected = Arrays.asList(
            101,103,107,109,113,127,131,137,139,149,151,
            157,163,167,173,179,181,191,193,197,199
        );
        List<Integer> actual = PrimeRange.primesInclusive(101, 200);
        require(actual.equals(expected), "fixed range mismatch: " + actual);
        require(actual.size() == 21, "count mismatch: " + actual.size());
        require(!PrimeRange.isPrime(1), "1 is not prime");
        require(PrimeRange.isPrime(2), "2 is prime");
        require(PrimeRange.isPrime(101), "101 is prime");
        require(!PrimeRange.isPrime(121), "121=11^2 is composite");
        require(!PrimeRange.isPrime(169), "169=13^2 is composite");
        require(!PrimeRange.isPrime(200), "200 is composite");
        require(PrimeRange.isPrime(199), "199 is prime");
        for (int n = -20; n <= 500; n++) {
            require(PrimeRange.isPrime(n) == oracle(n), "oracle mismatch at " + n);
        }
        require(PrimeRange.primesInclusive(5, 4).isEmpty(), "reversed range must be empty");
        System.out.println("PASS fixed-range=21 exact-list=yes oracle=-20..500 boundaries=yes square-composites=yes");
    }
}
