import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class ProducerConsumerDemoTest {
    public static void main(String[] args) throws Exception {
        singleConsumerFifo();
        multiConsumerExactlyOnce();
        emptyStillTerminatesAllConsumers();
        repeatedSmallCapacity();
        invalidArguments();
        System.out.println("PASS fifo=yes multi-exactly-once=yes empty-stop=yes repeated-capacity1=50 invalid=yes");
    }
    private static void singleConsumerFifo() throws Exception {
        var r=ProducerConsumerDemo.run(100,1,1);
        eq(range(100),r.consumed(),"single consumer FIFO");
        eq(1,r.stopMessages(),"single stop");
    }
    private static void multiConsumerExactlyOnce() throws Exception {
        var r=ProducerConsumerDemo.run(1000,4,7);
        var sorted=new ArrayList<>(r.consumed()); Collections.sort(sorted);
        eq(range(1000),sorted,"multi exactly once");
        eq(4,r.stopMessages(),"four stops");
    }
    private static void emptyStillTerminatesAllConsumers() throws Exception {
        var r=ProducerConsumerDemo.run(0,3,2);
        eq(List.of(),r.consumed(),"empty values"); eq(3,r.stopMessages(),"empty stops");
    }
    private static void repeatedSmallCapacity() throws Exception {
        for(int round=0;round<50;round++){
            var r=ProducerConsumerDemo.run(40,3,1);
            var sorted=new ArrayList<>(r.consumed()); Collections.sort(sorted);
            eq(range(40),sorted,"capacity1 round "+round); eq(3,r.stopMessages(),"capacity1 stops");
        }
    }
    private static void invalidArguments() {
        throwsIAE(() -> ProducerConsumerDemo.run(-1,1,1));
        throwsIAE(() -> ProducerConsumerDemo.run(1,0,1));
        throwsIAE(() -> ProducerConsumerDemo.run(1,1,0));
    }
    private static List<Integer> range(int n){var r=new ArrayList<Integer>();for(int i=1;i<=n;i++)r.add(i);return r;}
    private static void throwsIAE(Throwing r){try{r.run();throw new AssertionError("expected IllegalArgumentException");}catch(IllegalArgumentException expected){}catch(Exception e){throw new AssertionError(e);}}
    private static void eq(Object e,Object a,String label){if(!e.equals(a))throw new AssertionError(label+" expected="+e+" actual="+a);}
    @FunctionalInterface private interface Throwing { void run() throws Exception; }
}
