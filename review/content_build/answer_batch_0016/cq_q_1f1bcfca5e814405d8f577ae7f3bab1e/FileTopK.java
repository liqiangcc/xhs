import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.PriorityQueue;

public final class FileTopK {
    private FileTopK() {}

    public static List<Long> topK(Path path, int k) throws IOException {
        if (k <= 0) {
            throw new IllegalArgumentException("k must be positive");
        }

        PriorityQueue<Long> minHeap = new PriorityQueue<>(k);
        try (BufferedReader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                String text = line.trim();
                if (text.isEmpty()) {
                    continue;
                }
                long value = Long.parseLong(text);
                if (minHeap.size() < k) {
                    minHeap.add(value);
                } else if (value > minHeap.peek()) {
                    minHeap.poll();
                    minHeap.add(value);
                }
            }
        }

        List<Long> result = new ArrayList<>(minHeap);
        result.sort(Comparator.reverseOrder());
        return result;
    }
}
