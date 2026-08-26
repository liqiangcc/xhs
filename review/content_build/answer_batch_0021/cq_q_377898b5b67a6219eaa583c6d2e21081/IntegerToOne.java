public final class IntegerToOne {
    private IntegerToOne() {}

    public static int minOperations(int n) {
        if (n <= 0) {
            throw new IllegalArgumentException("n must be positive");
        }
        long x = n;
        int steps = 0;
        while (x != 1L) {
            if ((x & 1L) == 0L) {
                x >>= 1;
            } else if (x == 3L || (x & 3L) == 1L) {
                x--;
            } else {
                x++;
            }
            steps++;
        }
        return steps;
    }
}
