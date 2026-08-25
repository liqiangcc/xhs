import java.util.ArrayList;
import java.util.List;

public final class PrimeRange {
    private PrimeRange() {}

    public static boolean isPrime(int n) {
        if (n < 2) return false;
        if (n == 2) return true;
        if ((n & 1) == 0) return false;
        for (int d = 3; d <= n / d; d += 2) {
            if (n % d == 0) return false;
        }
        return true;
    }

    public static List<Integer> primesInclusive(int low, int high) {
        List<Integer> result = new ArrayList<>();
        if (low > high) return result;
        for (int n = low; n <= high; n++) {
            if (isPrime(n)) result.add(n);
            if (n == Integer.MAX_VALUE) break;
        }
        return result;
    }
}
