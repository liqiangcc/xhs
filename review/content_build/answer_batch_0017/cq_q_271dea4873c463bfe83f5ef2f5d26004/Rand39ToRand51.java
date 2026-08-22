public final class Rand39ToRand51 {
    private Rand39ToRand51() {}

    @FunctionalInterface
    public interface Rand39 {
        int next();
    }

    public static int nextRand51(Rand39 source) {
        if (source == null) {
            throw new IllegalArgumentException("source must not be null");
        }

        while (true) {
            int a = draw(source);
            int b = draw(source);
            int sample = a * 39 + b;
            if (sample < 1479) {
                return sample % 51;
            }
        }
    }

    private static int draw(Rand39 source) {
        int value = source.next();
        if (value < 0 || value >= 39) {
            throw new IllegalStateException("rand39 must return values in [0, 38]");
        }
        return value;
    }
}
