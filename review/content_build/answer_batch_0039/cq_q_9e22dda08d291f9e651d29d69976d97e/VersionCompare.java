public final class VersionCompare {
    private VersionCompare() {}

    public static int compareVersion(String left, String right) {
        if (left == null || right == null) {
            throw new IllegalArgumentException("version must not be null");
        }

        String[] a = left.split("\\.", -1);
        String[] b = right.split("\\.", -1);
        int n = Math.max(a.length, b.length);

        for (int i = 0; i < n; i++) {
            String x = i < a.length ? normalize(a[i]) : "0";
            String y = i < b.length ? normalize(b[i]) : "0";

            if (x.length() != y.length()) {
                return x.length() < y.length() ? -1 : 1;
            }
            int cmp = x.compareTo(y);
            if (cmp != 0) {
                return cmp < 0 ? -1 : 1;
            }
        }
        return 0;
    }

    private static String normalize(String segment) {
        if (segment.isEmpty()) {
            throw new IllegalArgumentException("empty revision");
        }
        for (int i = 0; i < segment.length(); i++) {
            char c = segment.charAt(i);
            if (c < '0' || c > '9') {
                throw new IllegalArgumentException("revision must contain only decimal digits");
            }
        }

        int i = 0;
        while (i < segment.length() - 1 && segment.charAt(i) == '0') {
            i++;
        }
        return segment.substring(i);
    }
}
