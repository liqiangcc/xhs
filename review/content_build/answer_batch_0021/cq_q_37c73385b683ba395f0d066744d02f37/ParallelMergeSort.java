import java.util.Arrays;
import java.util.Objects;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.RecursiveAction;

public final class ParallelMergeSort {
    private ParallelMergeSort() {}

    public static void sort(int[] values, int parallelism, int threshold) {
        Objects.requireNonNull(values, "values");
        if (parallelism < 1) throw new IllegalArgumentException("parallelism must be >= 1");
        if (threshold < 1) throw new IllegalArgumentException("threshold must be >= 1");
        if (values.length < 2) return;

        int[] tmp = new int[values.length];
        ForkJoinPool pool = new ForkJoinPool(parallelism);
        try {
            pool.invoke(new SortTask(values, tmp, 0, values.length, threshold));
        } finally {
            pool.shutdown();
        }
    }

    private static final class SortTask extends RecursiveAction {
        private static final long serialVersionUID = 1L;
        private final int[] a;
        private final int[] tmp;
        private final int lo;
        private final int hi;
        private final int threshold;

        SortTask(int[] a, int[] tmp, int lo, int hi, int threshold) {
            this.a = a;
            this.tmp = tmp;
            this.lo = lo;
            this.hi = hi;
            this.threshold = threshold;
        }

        @Override
        protected void compute() {
            int len = hi - lo;
            if (len <= threshold) {
                Arrays.sort(a, lo, hi);
                return;
            }

            int mid = lo + (len >>> 1);
            invokeAll(
                new SortTask(a, tmp, lo, mid, threshold),
                new SortTask(a, tmp, mid, hi, threshold)
            );
            merge(a, tmp, lo, mid, hi);
        }
    }

    private static void merge(int[] a, int[] tmp, int lo, int mid, int hi) {
        int i = lo;
        int j = mid;
        int k = lo;
        while (i < mid && j < hi) {
            tmp[k++] = a[i] <= a[j] ? a[i++] : a[j++];
        }
        while (i < mid) tmp[k++] = a[i++];
        while (j < hi) tmp[k++] = a[j++];
        System.arraycopy(tmp, lo, a, lo, hi - lo);
    }
}
