import java.util.ArrayList;
import java.util.List;

public final class SpiralMatrixTraversal {
    private SpiralMatrixTraversal() {}

    /**
     * Returns the elements of a rectangular int matrix in clockwise spiral order,
     * beginning at the top-left corner. Null/empty matrices return an empty list.
     * Null rows or ragged row lengths are rejected because this candidate chooses
     * an explicit rectangular-matrix API; the interview source does not define them.
     */
    public static List<Integer> spiralOrder(int[][] matrix) {
        List<Integer> result = new ArrayList<>();
        if (matrix == null || matrix.length == 0) {
            return result;
        }
        if (matrix[0] == null) {
            throw new IllegalArgumentException("matrix rows must be non-null");
        }

        int columns = matrix[0].length;
        for (int row = 1; row < matrix.length; row++) {
            if (matrix[row] == null || matrix[row].length != columns) {
                throw new IllegalArgumentException(
                        "matrix must be rectangular with non-null rows");
            }
        }
        if (columns == 0) {
            return result;
        }

        int top = 0;
        int bottom = matrix.length - 1;
        int left = 0;
        int right = columns - 1;

        while (top <= bottom && left <= right) {
            for (int column = left; column <= right; column++) {
                result.add(matrix[top][column]);
            }
            top++;

            for (int row = top; row <= bottom; row++) {
                result.add(matrix[row][right]);
            }
            right--;

            if (top <= bottom) {
                for (int column = right; column >= left; column--) {
                    result.add(matrix[bottom][column]);
                }
                bottom--;
            }

            if (left <= right) {
                for (int row = bottom; row >= top; row--) {
                    result.add(matrix[row][left]);
                }
                left++;
            }
        }

        return result;
    }
}
