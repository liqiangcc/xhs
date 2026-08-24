public final class MinPowerOfTwoOperations {
    private MinPowerOfTwoOperations() {}

    public static int minOperations(int value) {
        long v = Math.abs((long) value);
        int operations = 0;

        while (v != 0) {
            if ((v & 1L) == 0L) {
                v >>= 1;
                continue;
            }

            operations++;
            if (v == 1L) {
                break;
            }

            if ((v & 3L) == 1L) {
                v = (v - 1L) >> 1;
            } else {
                v = (v + 1L) >> 1;
            }
        }
        return operations;
    }
}
