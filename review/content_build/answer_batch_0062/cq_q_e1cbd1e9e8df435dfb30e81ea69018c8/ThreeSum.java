import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class ThreeSum {
    public static List<List<Integer>> threeSum(int[] nums) {
        List<List<Integer>> ans = new ArrayList<>();
        if (nums == null || nums.length < 3) return ans;
        int[] a = nums.clone();
        Arrays.sort(a);
        for (int i = 0; i < a.length - 2; i++) {
            if (i > 0 && a[i] == a[i - 1]) continue;
            if (a[i] > 0) break;
            int left = i + 1, right = a.length - 1;
            while (left < right) {
                long sum = (long) a[i] + a[left] + a[right];
                if (sum < 0) {
                    left++;
                } else if (sum > 0) {
                    right--;
                } else {
                    ans.add(List.of(a[i], a[left], a[right]));
                    int lv = a[left], rv = a[right];
                    while (left < right && a[left] == lv) left++;
                    while (left < right && a[right] == rv) right--;
                }
            }
        }
        return ans;
    }
}
