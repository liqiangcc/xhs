public final class BPlusTreeSizing {
    private BPlusTreeSizing() {}

    public static int maxFanout(long usableInternalBytes, long keyBytes, long childPointerBytes) {
        requirePositive(usableInternalBytes, "usableInternalBytes");
        requirePositive(keyBytes, "keyBytes");
        requirePositive(childPointerBytes, "childPointerBytes");
        long fanout = (usableInternalBytes + keyBytes) / (keyBytes + childPointerBytes);
        if (fanout < 2 || fanout > Integer.MAX_VALUE) throw new IllegalArgumentException("fanout outside supported range");
        return (int) fanout;
    }

    public static int leafCapacity(long usableLeafBytes, long leafEntryBytes) {
        requirePositive(usableLeafBytes, "usableLeafBytes");
        requirePositive(leafEntryBytes, "leafEntryBytes");
        long capacity = usableLeafBytes / leafEntryBytes;
        if (capacity < 1 || capacity > Integer.MAX_VALUE) throw new IllegalArgumentException("leaf capacity outside supported range");
        return (int) capacity;
    }

    public static int minimumFullLevels(long records, int fanout, int leafCapacity) {
        if (records < 0) throw new IllegalArgumentException("records must be non-negative");
        if (fanout < 2) throw new IllegalArgumentException("fanout must be at least 2");
        if (leafCapacity < 1) throw new IllegalArgumentException("leafCapacity must be positive");
        if (records <= leafCapacity) return 1;
        long capacity = leafCapacity;
        int levels = 1;
        while (capacity < records) {
            if (capacity > Long.MAX_VALUE / fanout) return levels + 1;
            capacity *= fanout;
            levels++;
        }
        return levels;
    }

    public static boolean fitsInternalNode(int fanout, long usableInternalBytes, long keyBytes, long childPointerBytes) {
        if (fanout < 1) return false;
        long pointerBytes = Math.multiplyExact((long) fanout, childPointerBytes);
        long separatorBytes = Math.multiplyExact((long) (fanout - 1), keyBytes);
        return Math.addExact(pointerBytes, separatorBytes) <= usableInternalBytes;
    }

    private static void requirePositive(long value, String name) {
        if (value <= 0) throw new IllegalArgumentException(name + " must be positive");
    }
}
