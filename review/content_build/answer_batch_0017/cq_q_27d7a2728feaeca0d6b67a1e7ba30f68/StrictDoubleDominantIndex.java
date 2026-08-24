public final class StrictDoubleDominantIndex {
    private StrictDoubleDominantIndex() {}

    public static int findFirst(int[] nums) {
        if (nums == null || nums.length == 0) {
            return -1;
        }
        if (nums.length == 1) {
            return 0;
        }

        int first = -1;
        int second = -1;
        for (int i = 0; i < nums.length; i++) {
            if (first == -1 || nums[i] > nums[first]) {
                second = first;
                first = i;
            } else if (second == -1 || nums[i] > nums[second]) {
                second = i;
            }
        }

        for (int i = 0; i < nums.length; i++) {
            int maxOther = (i == first) ? nums[second] : nums[first];
            if ((long) nums[i] > 2L * maxOther) {
                return i;
            }
        }
        return -1;
    }
}
