final class OddFrequencyNumbers {
    static int findOneOdd(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        int xor = 0;
        for (int x : nums) xor ^= x;
        return xor;
    }

    static int[] findTwoOdd(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        int xor = 0;
        for (int x : nums) xor ^= x;
        if (xor == 0) throw new IllegalArgumentException("contract requires exactly two distinct odd-frequency values");
        int lowbit = xor & -xor;
        int a = 0;
        int b = 0;
        for (int x : nums) {
            if ((x & lowbit) == 0) a ^= x;
            else b ^= x;
        }
        return new int[]{a, b};
    }
}
