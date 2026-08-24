import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Random;

public final class FileTopKTest {
    private static int fixed = 0;
    private static int randomized = 0;

    public static void main(String[] args) throws Exception {
        assertTopK(List.of(), 10);
        assertTopK(List.of(3L, 1L, 2L), 10);
        assertTopK(List.of(10L, 9L, 8L, 7L, 6L, 5L, 4L, 3L, 2L, 1L), 10);
        assertTopK(List.of(7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 6L, 8L), 10);
        assertTopK(List.of(-5L, -1L, -3L, -2L, -4L, 0L), 3);
        assertTopK(List.of(Long.MIN_VALUE, 0L, Long.MAX_VALUE, 1L, -1L), 2);
        assertTopKWithBlankLines(List.of(5L, 1L, 9L, 9L, -2L), 3);
        fixed += 7;

        Random random = new Random(0x1F1BCFCAL);
        for (int round = 0; round < 5000; round++) {
            int n = random.nextInt(250);
            int k = 1 + random.nextInt(20);
            List<Long> values = new ArrayList<>(n);
            for (int i = 0; i < n; i++) {
                values.add((long) random.nextInt(2001) - 1000L);
            }
            assertTopK(values, k);
            randomized++;
        }

        assertThrowsNumberFormat();
        assertThrowsInvalidK();

        System.out.println("PASS fixed=" + fixed
                + " randomized=" + randomized
                + " oracle=full-sort-prefix duplicate_semantics=occurrence-preserving");
    }

    private static void assertTopK(List<Long> input, int k) throws Exception {
        Path file = Files.createTempFile("file-top-k-", ".txt");
        try {
            List<String> lines = input.stream().map(String::valueOf).toList();
            Files.write(file, lines, StandardCharsets.UTF_8);
            List<Long> actual = FileTopK.topK(file, k);
            List<Long> expected = oracle(input, k);
            if (!actual.equals(expected)) {
                throw new AssertionError("input=" + input + " k=" + k
                        + " expected=" + expected + " actual=" + actual);
            }
        } finally {
            Files.deleteIfExists(file);
        }
    }

    private static void assertTopKWithBlankLines(List<Long> input, int k) throws Exception {
        Path file = Files.createTempFile("file-top-k-blanks-", ".txt");
        try {
            List<String> lines = new ArrayList<>();
            lines.add("");
            for (Long value : input) {
                lines.add("  " + value + "  ");
                lines.add("   ");
            }
            Files.write(file, lines, StandardCharsets.UTF_8);
            List<Long> actual = FileTopK.topK(file, k);
            List<Long> expected = oracle(input, k);
            if (!actual.equals(expected)) {
                throw new AssertionError("blank-line fixture expected=" + expected + " actual=" + actual);
            }
        } finally {
            Files.deleteIfExists(file);
        }
    }

    private static List<Long> oracle(List<Long> input, int k) {
        List<Long> sorted = new ArrayList<>(input);
        sorted.sort(Comparator.reverseOrder());
        return new ArrayList<>(sorted.subList(0, Math.min(k, sorted.size())));
    }

    private static void assertThrowsNumberFormat() throws IOException {
        Path file = Files.createTempFile("file-top-k-invalid-", ".txt");
        try {
            Files.writeString(file, "1\nnot-a-number\n2\n", StandardCharsets.UTF_8);
            try {
                FileTopK.topK(file, 10);
                throw new AssertionError("expected NumberFormatException");
            } catch (NumberFormatException expected) {
                // expected
            }
        } finally {
            Files.deleteIfExists(file);
        }
    }

    private static void assertThrowsInvalidK() throws IOException {
        Path file = Files.createTempFile("file-top-k-k-", ".txt");
        try {
            Files.writeString(file, "1\n", StandardCharsets.UTF_8);
            try {
                FileTopK.topK(file, 0);
                throw new AssertionError("expected IllegalArgumentException");
            } catch (IllegalArgumentException expected) {
                // expected
            }
        } finally {
            Files.deleteIfExists(file);
        }
    }
}
