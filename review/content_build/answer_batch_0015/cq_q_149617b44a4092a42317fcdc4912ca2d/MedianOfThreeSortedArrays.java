import java.util.Objects;

public final class MedianOfThreeSortedArrays {
    private MedianOfThreeSortedArrays() {}

    public static double median(int[] first, int[] second, int[] third) {
        Objects.requireNonNull(first, "first");
        Objects.requireNonNull(second, "second");
        Objects.requireNonNull(third, "third");

        int total = first.length + second.length + third.length;
        if (total == 0) {
            throw new IllegalArgumentException("at least one value is required");
        }

        int leftTarget = (total - 1) / 2;
        int rightTarget = total / 2;
        int i = 0;
        int j = 0;
        int k = 0;
        int leftValue = 0;
        int rightValue = 0;

        for (int rank = 0; rank <= rightTarget; rank++) {
            int source = -1;
            int value = 0;

            if (i < first.length) {
                source = 0;
                value = first[i];
            }
            if (j < second.length && (source < 0 || second[j] < value)) {
                source = 1;
                value = second[j];
            }
            if (k < third.length && (source < 0 || third[k] < value)) {
                source = 2;
                value = third[k];
            }

            if (source == 0) {
                i++;
            } else if (source == 1) {
                j++;
            } else if (source == 2) {
                k++;
            } else {
                throw new IllegalStateException("no next value");
            }

            if (rank == leftTarget) {
                leftValue = value;
            }
            if (rank == rightTarget) {
                rightValue = value;
            }
        }

        return ((long) leftValue + rightValue) / 2.0;
    }
}
