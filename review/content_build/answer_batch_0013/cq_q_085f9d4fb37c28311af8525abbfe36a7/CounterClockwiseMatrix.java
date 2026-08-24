import java.util.ArrayList;
import java.util.List;

public final class CounterClockwiseMatrix {
    public static List<Integer> fromTopLeft(int[][] matrix) {
        List<Integer> result = new ArrayList<>();
        if (matrix == null || matrix.length == 0) {
            return result;
        }

        int cols = validateRectangular(matrix);
        if (cols == 0) {
            return result;
        }

        int top = 0;
        int bottom = matrix.length - 1;
        int left = 0;
        int right = cols - 1;

        while (top <= bottom && left <= right) {
            for (int row = top; row <= bottom; row++) {
                result.add(matrix[row][left]);
            }
            left++;

            if (top <= bottom && left <= right) {
                for (int col = left; col <= right; col++) {
                    result.add(matrix[bottom][col]);
                }
                bottom--;
            }

            if (top <= bottom && left <= right) {
                for (int row = bottom; row >= top; row--) {
                    result.add(matrix[row][right]);
                }
                right--;
            }

            if (top <= bottom && left <= right) {
                for (int col = right; col >= left; col--) {
                    result.add(matrix[top][col]);
                }
                top++;
            }
        }
        return result;
    }

    private static int validateRectangular(int[][] matrix) {
        if (matrix[0] == null) {
            throw new IllegalArgumentException("matrix rows must be non-null");
        }
        int cols = matrix[0].length;
        for (int row = 1; row < matrix.length; row++) {
            if (matrix[row] == null || matrix[row].length != cols) {
                throw new IllegalArgumentException("matrix must be rectangular");
            }
        }
        return cols;
    }
}
