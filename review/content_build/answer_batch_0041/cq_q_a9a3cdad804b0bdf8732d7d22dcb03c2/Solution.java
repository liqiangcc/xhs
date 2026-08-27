final class Solution {
    static void sortDescending(int[] a) {
        if (a == null) throw new IllegalArgumentException("array must not be null");
        int n = a.length;
        for (int i = n / 2 - 1; i >= 0; i--) {
            siftDown(a, i, n);
        }
        for (int end = n - 1; end > 0; end--) {
            swap(a, 0, end);
            siftDown(a, 0, end);
        }
    }

    private static void siftDown(int[] a, int root, int size) {
        while (true) {
            int left = root * 2 + 1;
            if (left >= size) return;
            int right = left + 1;
            int smaller = left;
            if (right < size && a[right] < a[left]) {
                smaller = right;
            }
            if (a[root] <= a[smaller]) return;
            swap(a, root, smaller);
            root = smaller;
        }
    }

    private static void swap(int[] a, int i, int j) {
        int t = a[i];
        a[i] = a[j];
        a[j] = t;
    }
}
