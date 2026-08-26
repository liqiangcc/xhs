import java.util.Random;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public final class RoundRobinABCWriterTest {
    public static void main(String[] args) throws Exception {
        check(0);
        check(1);
        check(2);
        check(1000);
        boolean negative=false;
        try { RoundRobinABC.print(-1); } catch (IllegalArgumentException e) { negative=true; }
        if(!negative) throw new AssertionError("negative rounds must reject");

        Random r=new Random(0x89D62736L);
        for(int i=0;i<200;i++) check(r.nextInt(150));
        System.out.println("PASS fixed=4 random=200 exact-order=pass zero=pass negative=reject timeout=pass");
    }

    private static void check(int rounds) throws Exception {
        ExecutorService executor=Executors.newSingleThreadExecutor();
        Future<String> future=executor.submit(() -> RoundRobinABC.print(rounds));
        try {
            String actual=future.get(3,TimeUnit.SECONDS);
            String expected="ABC".repeat(rounds);
            if(!actual.equals(expected)) throw new AssertionError("rounds="+rounds+" actual="+actual+" expected="+expected);
        } catch (TimeoutException e) {
            future.cancel(true);
            throw new AssertionError("deadlock/timeout rounds="+rounds,e);
        } catch (ExecutionException e) {
            throw new AssertionError("worker execution failed rounds="+rounds,e.getCause());
        } finally {
            executor.shutdownNow();
            if(!executor.awaitTermination(3,TimeUnit.SECONDS)) throw new AssertionError("test executor did not terminate");
        }
    }
}
