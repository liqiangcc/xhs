public final class SpiralMatrixII {
    private SpiralMatrixII() {}

    public static int[][] generateMatrix(int n) {
        if (n <= 0) throw new IllegalArgumentException("n must be positive");
        int[][] matrix = new int[n][n];
        int top = 0, bottom = n - 1, left = 0, right = n - 1, value = 1;
        while (top <= bottom && left <= right) {
            for (int col = left; col <= right; col++) matrix[top][col] = value++;
            top++;
            for (int row = top; row <= bottom; row++) matrix[row][right] = value++;
            right--;
            if (top <= bottom) {
                for (int col = right; col >= left; col--) matrix[bottom][col] = value++;
                bottom--;
            }
            if (left <= right) {
                for (int row = bottom; row >= top; row--) matrix[row][left] = value++;
                left++;
            }
        }
        return matrix;
    }
}
