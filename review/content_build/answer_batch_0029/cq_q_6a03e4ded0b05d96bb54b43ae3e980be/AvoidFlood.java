import java.util.HashMap;
import java.util.Map;
import java.util.TreeSet;

final class AvoidFlood {
    static int[] avoidFlood(int[] rains) {
        if (rains == null) throw new IllegalArgumentException("rains must not be null");
        int n = rains.length;
        int[] ans = new int[n];
        Map<Integer, Integer> lastRain = new HashMap<>();
        TreeSet<Integer> dryDays = new TreeSet<>();
        for (int i = 0; i < n; i++) {
            int lake = rains[i];
            if (lake < 0) throw new IllegalArgumentException("rains[i] must be >= 0");
            if (lake == 0) {
                ans[i] = 1;
                dryDays.add(i);
                continue;
            }
            ans[i] = -1;
            Integer prev = lastRain.put(lake, i);
            if (prev == null) continue;
            Integer dry = dryDays.higher(prev);
            if (dry == null) return new int[0];
            ans[dry] = lake;
            dryDays.remove(dry);
        }
        return ans;
    }
}
