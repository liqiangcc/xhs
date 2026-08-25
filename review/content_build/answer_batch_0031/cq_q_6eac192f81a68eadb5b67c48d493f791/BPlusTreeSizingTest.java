import java.math.BigInteger;
import java.util.Random;

public final class BPlusTreeSizingTest {
    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    private static int bruteFanout(long usable, long key, long pointer) {
        int best = 0;
        for (int f = 1; f < 1_000_000; f++) {
            BigInteger bytes = BigInteger.valueOf(f).multiply(BigInteger.valueOf(pointer))
                    .add(BigInteger.valueOf(f - 1L).multiply(BigInteger.valueOf(key)));
            if (bytes.compareTo(BigInteger.valueOf(usable)) <= 0) best = f; else break;
        }
        return best;
    }

    private static int bigIntegerLevels(long records, int fanout, int leafCapacity) {
        if (records <= leafCapacity) return 1;
        BigInteger target = BigInteger.valueOf(records);
        BigInteger capacity = BigInteger.valueOf(leafCapacity);
        int levels = 1;
        while (capacity.compareTo(target) < 0) {
            capacity = capacity.multiply(BigInteger.valueOf(fanout));
            levels++;
        }
        return levels;
    }

    public static void main(String[] args) {
        require(BPlusTreeSizing.maxFanout(4000, 16, 8) == 167, "fixed fanout");
        require(BPlusTreeSizing.leafCapacity(4000, 64) == 62, "fixed leaf capacity");
        require(BPlusTreeSizing.minimumFullLevels(1_000_000, 167, 62) == 3, "fixed levels");
        require(BPlusTreeSizing.fitsInternalNode(167, 4000, 16, 8), "167 should fit");
        require(!BPlusTreeSizing.fitsInternalNode(168, 4000, 16, 8), "168 should not fit");
        require(BPlusTreeSizing.minimumFullLevels(62, 167, 62) == 1, "root leaf boundary");
        require(BPlusTreeSizing.minimumFullLevels(63, 167, 62) == 2, "first second-level boundary");

        Random random = new Random(20260825L);
        int fanoutCases = 0;
        for (int i = 0; i < 2000; i++) {
            long usable = 512 + random.nextInt(16_000);
            long key = 1 + random.nextInt(64);
            long pointer = 1 + random.nextInt(32);
            int expected = bruteFanout(usable, key, pointer);
            if (expected < 2) continue;
            int actual = BPlusTreeSizing.maxFanout(usable, key, pointer);
            require(actual == expected, "fanout mismatch usable=" + usable + " key=" + key + " ptr=" + pointer + " actual=" + actual + " expected=" + expected);
            require(BPlusTreeSizing.fitsInternalNode(actual, usable, key, pointer), "computed fanout should fit");
            require(!BPlusTreeSizing.fitsInternalNode(actual + 1, usable, key, pointer), "computed fanout must be maximal");
            fanoutCases++;
        }

        int heightCases = 0;
        for (int i = 0; i < 5000; i++) {
            int fanout = 2 + random.nextInt(500);
            int leaf = 1 + random.nextInt(500);
            long records = 1 + Math.floorMod(random.nextLong(), 1_000_000_000L);
            int expected = bigIntegerLevels(records, fanout, leaf);
            int actual = BPlusTreeSizing.minimumFullLevels(records, fanout, leaf);
            require(actual == expected, "height mismatch records=" + records + " fanout=" + fanout + " leaf=" + leaf + " actual=" + actual + " expected=" + expected);
            heightCases++;
        }

        boolean badFanout = false, badLeaf = false, badHeight = false;
        try { BPlusTreeSizing.maxFanout(100, 100, 100); } catch (IllegalArgumentException expected) { badFanout = true; }
        try { BPlusTreeSizing.leafCapacity(10, 20); } catch (IllegalArgumentException expected) { badLeaf = true; }
        try { BPlusTreeSizing.minimumFullLevels(-1, 3, 4); } catch (IllegalArgumentException expected) { badHeight = true; }
        require(badFanout && badLeaf && badHeight, "invalid parameter guards");

        System.out.println("PASS fixed=7 fanout-oracle=" + fanoutCases + " height-oracle=" + heightCases + " model=f-child-pointers-plus-f-minus-1-keys validation=yes");
    }
}
