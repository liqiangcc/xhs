import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public final class ProducerConsumerDemo {
    private record Message(int value, boolean stop) {
        static Message item(int value) { return new Message(value, false); }
        static Message stopMessage() { return new Message(0, true); }
    }
    public record Result(List<Integer> consumed, int stopMessages) {}

    public static Result run(int itemCount, int consumerCount, int capacity) throws Exception {
        if (itemCount < 0 || consumerCount < 1 || capacity < 1) throw new IllegalArgumentException("invalid simulation arguments");
        BlockingQueue<Message> queue = new ArrayBlockingQueue<>(capacity);
        ConcurrentLinkedQueue<Integer> consumed = new ConcurrentLinkedQueue<>();
        ExecutorService pool = Executors.newFixedThreadPool(consumerCount + 1);
        List<Future<Void>> consumerFutures = new ArrayList<>();
        try {
            for (int c = 0; c < consumerCount; c++) {
                consumerFutures.add(pool.submit(() -> {
                    while (true) {
                        Message message = queue.take();
                        if (message.stop()) return null;
                        consumed.add(message.value());
                    }
                }));
            }
            Future<Void> producer = pool.submit(() -> {
                for (int value = 1; value <= itemCount; value++) queue.put(Message.item(value));
                for (int c = 0; c < consumerCount; c++) queue.put(Message.stopMessage());
                return null;
            });
            producer.get(5, TimeUnit.SECONDS);
            for (Future<Void> consumer : consumerFutures) consumer.get(5, TimeUnit.SECONDS);
            return new Result(List.copyOf(consumed), consumerCount);
        } finally {
            pool.shutdownNow();
        }
    }
}
