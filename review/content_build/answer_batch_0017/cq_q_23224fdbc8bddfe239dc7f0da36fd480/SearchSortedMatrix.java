public final class SearchSortedMatrix {
    private SearchSortedMatrix() {}

    /**
     * Returns whether target exists in a rectangular matrix whose rows and columns
     * are each nondecreasing. Null/empty matrices are treated as not containing
     * any target. Ragged matrices or null rows are rejected because the interview
     * source does not define those shapes and this candidate chooses a rectangular API.
     */
    public static boolean contains(int[][] matrix, int target) {
        if (matrix == null || matrix.length == 0) {
            return false;
        }
        if (matrix[0] == null) {
            throw new IllegalArgumentException("matrix rows must be non-null");
        }
        final int columns = matrix[0].length;
        for (int row = 1; row < matrix.length; row++) {
            if (matrix[row] == null || matrix[row].length != columns) {
                throw new IllegalArgumentException("matrix must be rectangular with non-null rows");
            }
        }
        if (columns == 0) {
            return false;
        }

        int row = 0;
        int column = columns - 1;
        while (row < matrix.length && column >= 0) {
            int value = matrix[row][column];
            if (value == target) {
                return true;
            }
            if (value > target) {
                column--;
            } else {
                row++;
            }
        }
        return false;
    }
}
