public final class OddFrequencyXor {
    public static int findOddFrequency(int[] a) {
        if (a == null || a.length == 0) throw new IllegalArgumentException("array must be non-empty");
        int ans=0; for(int x:a) ans^=x; return ans;
    }
}
