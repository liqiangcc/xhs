import java.util.Objects;

public final class ReverseArray {
    private ReverseArray() {}

    public static void reverseInPlace(int[] values) {
        Objects.requireNonNull(values, "values");
        int left = 0;
        int right = values.length - 1;
        while (left < right) {
            int tmp = values[left];
            values[left] = values[right];
            values[right] = tmp;
            left++;
            right--;
        }
    }

    public static int[] reversedCopy(int[] values) {
        Objects.requireNonNull(values, "values");
        int[] result = new int[values.length];
        for (int i = 0; i < values.length; i++) {
            result[i] = values[values.length - 1 - i];
        }
        return result;
    }
}
