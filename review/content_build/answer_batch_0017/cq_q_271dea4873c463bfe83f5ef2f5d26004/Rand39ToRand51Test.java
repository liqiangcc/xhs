import java.util.Arrays;
import java.util.Random;

public final class Rand39ToRand51Test {
    public static void main(String[] args) {
        int[] exactCounts = verifyExhaustiveStatePartition();
        verifyImplementationForEveryAcceptedPair();
        verifyRejectionPath();
        verifyInvalidSources();
        int sampled = verifyDeterministicDistribution();
        System.out.printf(
                "PASS exhaustive=1521 accepted=1479 rejected=42 perBucket=%d sampled=%d%n",
                exactCounts[0],
                sampled);
    }

    private static int[] verifyExhaustiveStatePartition() {
        int[] counts = new int[51];
        int accepted = 0;
        int rejected = 0;
        for (int a = 0; a < 39; a++) {
            for (int b = 0; b < 39; b++) {
                int sample = a * 39 + b;
                if (sample < 1479) {
                    counts[sample % 51]++;
                    accepted++;
                } else {
                    rejected++;
                }
            }
        }
        if (accepted != 1479 || rejected != 42) {
            throw new AssertionError(
                    "partition accepted=" + accepted + " rejected=" + rejected);
        }
        for (int count : counts) {
            if (count != 29) {
                throw new AssertionError("bucket count=" + count + " expected=29");
            }
        }
        return counts;
    }

    private static void verifyImplementationForEveryAcceptedPair() {
        for (int a = 0; a < 39; a++) {
            for (int b = 0; b < 39; b++) {
                int sample = a * 39 + b;
                if (sample >= 1479) {
                    continue;
                }
                ScriptedRand39 source = new ScriptedRand39(a, b);
                int actual = Rand39ToRand51.nextRand51(source);
                int expected = sample % 51;
                if (actual != expected || source.calls() != 2) {
                    throw new AssertionError(
                            "pair a=" + a + " b=" + b
                                    + " expected=" + expected
                                    + " actual=" + actual
                                    + " calls=" + source.calls());
                }
            }
        }
    }

    private static void verifyRejectionPath() {
        ScriptedRand39 source = new ScriptedRand39(37, 36, 0, 0);
        int actual = Rand39ToRand51.nextRand51(source);
        if (actual != 0 || source.calls() != 4) {
            throw new AssertionError(
                    "rejection path expected result=0 calls=4 actual="
                            + actual + " calls=" + source.calls());
        }

        ScriptedRand39 lastAccepted = new ScriptedRand39(37, 35);
        int last = Rand39ToRand51.nextRand51(lastAccepted);
        if (last != 50 || lastAccepted.calls() != 2) {
            throw new AssertionError("last accepted state expected result=50");
        }
    }

    private static void verifyInvalidSources() {
        expectIllegalArgument(() -> Rand39ToRand51.nextRand51(null));
        expectIllegalState(() -> Rand39ToRand51.nextRand51(() -> -1));
        expectIllegalState(() -> Rand39ToRand51.nextRand51(() -> 39));
    }

    private static int verifyDeterministicDistribution() {
        Random random = new Random(20260823L);
        Rand39ToRand51.Rand39 source = () -> random.nextInt(39);
        int sampleCount = 510_000;
        int[] counts = new int[51];
        for (int i = 0; i < sampleCount; i++) {
            int value = Rand39ToRand51.nextRand51(source);
            if (value < 0 || value >= 51) {
                throw new AssertionError("out of range: " + value);
            }
            counts[value]++;
        }
        int expected = sampleCount / 51;
        int tolerance = expected / 20; // 5%, deliberately loose; exact uniformity is proved above.
        for (int i = 0; i < counts.length; i++) {
            if (Math.abs(counts[i] - expected) > tolerance) {
                throw new AssertionError(
                        "distribution bucket=" + i
                                + " count=" + counts[i]
                                + " expected=" + expected
                                + " tolerance=" + tolerance
                                + " all=" + Arrays.toString(counts));
            }
        }
        return sampleCount;
    }

    private static void expectIllegalArgument(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    private static void expectIllegalState(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected IllegalStateException");
        } catch (IllegalStateException expected) {
            // expected
        }
    }

    private static final class ScriptedRand39 implements Rand39ToRand51.Rand39 {
        private final int[] values;
        private int index;

        private ScriptedRand39(int... values) {
            this.values = values;
        }

        @Override
        public int next() {
            if (index >= values.length) {
                throw new AssertionError("script exhausted");
            }
            return values[index++];
        }

        private int calls() {
            return index;
        }
    }
}
