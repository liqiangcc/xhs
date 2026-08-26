import java.time.Duration;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public final class AlternatingWriterTest {
    private static long runs;
    public static void main(String[] args) throws Exception {
        Solution s=new Solution();
        verifyTimed(() -> s.withSemaphores(0), "");
        verifyTimed(() -> s.withWaitNotify(0), "");
        for(int pairs: new int[]{1,4,1000}) {
            String expected="ab".repeat(pairs);
            verifyTimed(() -> s.withSemaphores(pairs),expected);
            verifyTimed(() -> s.withWaitNotify(pairs),expected);
        }
        for(int round=0;round<120;round++) {
            int pairs=1+(round*37)%401;
            String expected="ab".repeat(pairs);
            verifyTimed(() -> s.withSemaphores(pairs),expected);
            verifyTimed(() -> s.withWaitNotify(pairs),expected);
        }
        boolean bad1=false,bad2=false;
        try{s.withSemaphores(-1);}catch(IllegalArgumentException e){bad1=true;}
        try{s.withWaitNotify(-1);}catch(IllegalArgumentException e){bad2=true;}
        if(!bad1||!bad2)throw new AssertionError("negative pairs not rejected");
        System.out.printf("PASS deterministic=8 stress_runs=%d start_b_first=pass exact_alternation=pass negative=pass%n",runs);
    }
    static void verifyTimed(Callable<String> call,String expected)throws Exception{
        ExecutorService ex=Executors.newSingleThreadExecutor();
        try{Future<String> f=ex.submit(call);String actual=f.get(Duration.ofSeconds(4).toMillis(),TimeUnit.MILLISECONDS);if(!actual.equals(expected))throw new AssertionError("len="+actual.length()+" expectedLen="+expected.length()+" actualPrefix="+actual.substring(0,Math.min(40,actual.length())));runs++;}
        finally{ex.shutdownNow();ex.awaitTermination(1,TimeUnit.SECONDS);}
    }
}
