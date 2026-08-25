import java.util.*;

public final class ModeMedian {
    public static final class Result {
        public final List<Integer> modes;
        public final double median;

        Result(List<Integer> modes, double median) {
            this.modes = Collections.unmodifiableList(new ArrayList<>(modes));
            this.median = median;
        }
    }

    public static Result solve(int[] nums) {
        if (nums == null || nums.length == 0) {
            throw new IllegalArgumentException("nums must not be null or empty");
        }

        Map<Integer, Integer> freq = new HashMap<>();
        int maxFreq = 0;
        for (int x : nums) {
            int f = freq.getOrDefault(x, 0) + 1;
            freq.put(x, f);
            if (f > maxFreq) maxFreq = f;
        }

        List<Integer> modes = new ArrayList<>();
        for (Map.Entry<Integer, Integer> e : freq.entrySet()) {
            if (e.getValue() == maxFreq) modes.add(e.getKey());
        }
        Collections.sort(modes);

        int k = modes.size();
        double median;
        if ((k & 1) == 1) {
            median = modes.get(k / 2);
        } else {
            median = ((long) modes.get(k / 2 - 1) + modes.get(k / 2)) / 2.0;
        }
        return new Result(modes, median);
    }
}
