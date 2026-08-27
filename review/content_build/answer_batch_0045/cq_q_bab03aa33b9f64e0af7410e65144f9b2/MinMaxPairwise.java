public final class MinMaxPairwise {
    public static int[] minMax(int[] a) {
        if (a == null || a.length == 0) throw new IllegalArgumentException("array must be non-empty");
        int min,max,i;
        if ((a.length & 1) == 0) {
            if (a[0] <= a[1]) { min=a[0]; max=a[1]; } else { min=a[1]; max=a[0]; }
            i=2;
        } else { min=max=a[0]; i=1; }
        while (i < a.length) {
            int small,large;
            if (a[i] <= a[i+1]) { small=a[i]; large=a[i+1]; } else { small=a[i+1]; large=a[i]; }
            if (small < min) min=small;
            if (large > max) max=large;
            i+=2;
        }
        return new int[]{min,max};
    }
}
