public final class Axis0Stats {
    public record Stats(double[] mean, double[] variance) {}

    public static Stats population(double[][] data) {
        if (data == null || data.length == 0) {
            throw new IllegalArgumentException("data must have at least one row");
        }
        if (data[0] == null || data[0].length == 0) {
            throw new IllegalArgumentException("data must have at least one column");
        }
        int rows = data.length;
        int cols = data[0].length;
        double[] mean = new double[cols];
        double[] m2 = new double[cols];

        for (int r = 0; r < rows; r++) {
            if (data[r] == null || data[r].length != cols) {
                throw new IllegalArgumentException("data must be rectangular");
            }
            int n = r + 1;
            for (int c = 0; c < cols; c++) {
                double x = data[r][c];
                if (!Double.isFinite(x)) {
                    throw new IllegalArgumentException("data must contain finite values");
                }
                double delta = x - mean[c];
                mean[c] += delta / n;
                double delta2 = x - mean[c];
                m2[c] += delta * delta2;
            }
        }

        double[] variance = new double[cols];
        for (int c = 0; c < cols; c++) {
            variance[c] = m2[c] / rows;
        }
        return new Stats(mean, variance);
    }
}
