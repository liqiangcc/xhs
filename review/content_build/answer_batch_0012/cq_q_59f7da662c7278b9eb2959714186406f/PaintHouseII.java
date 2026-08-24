public final class PaintHouseII {
    private PaintHouseII() {}

    public static int minCostII(int[][] costs) {
        if (costs == null) {
            throw new IllegalArgumentException("costs must not be null");
        }
        if (costs.length == 0) {
            return 0;
        }
        if (costs[0] == null || costs[0].length == 0) {
            throw new IllegalArgumentException("each house must have at least one color");
        }

        int colors = costs[0].length;
        for (int[] row : costs) {
            if (row == null || row.length != colors) {
                throw new IllegalArgumentException("cost matrix must be rectangular");
            }
        }
        if (colors == 1 && costs.length > 1) {
            throw new IllegalArgumentException("no valid coloring exists with one color and adjacent houses");
        }

        long[] previous = new long[colors];
        for (int color = 0; color < colors; color++) {
            previous[color] = costs[0][color];
        }

        for (int house = 1; house < costs.length; house++) {
            long min1 = Long.MAX_VALUE;
            long min2 = Long.MAX_VALUE;
            int minColor = -1;

            for (int color = 0; color < colors; color++) {
                long value = previous[color];
                if (value < min1) {
                    min2 = min1;
                    min1 = value;
                    minColor = color;
                } else if (value < min2) {
                    min2 = value;
                }
            }

            long[] current = new long[colors];
            for (int color = 0; color < colors; color++) {
                long bestPrevious = color == minColor ? min2 : min1;
                current[color] = Math.addExact(bestPrevious, costs[house][color]);
            }
            previous = current;
        }

        long answer = Long.MAX_VALUE;
        for (long value : previous) {
            answer = Math.min(answer, value);
        }
        return Math.toIntExact(answer);
    }
}
