import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Random;

public final class SimpleHashMapWriterTest {
    private record Key(int id, int hash) {
        @Override public int hashCode() { return hash; }
    }

    public static void main(String[] args) {
        SimpleHashMap<Key,String> map=new SimpleHashMap<>(4);
        Key a=new Key(1,7),b=new Key(2,7),c=new Key(3,-17);
        map.put(a,"A"); map.put(b,"B"); map.put(c,"C");
        eq(map.get(a),"A"); eq(map.get(b),"B"); eq(map.get(c),"C");
        map.put(b,"B2"); eq(map.get(b),"B2");
        if(map.get(new Key(99,7))!=null) throw new AssertionError("missing key must return null");
        expect(() -> new SimpleHashMap<Key,String>(0));
        expect(() -> map.put(null,"x"));
        expect(() -> map.put(a,null));
        expect(() -> map.get(null));

        SimpleHashMap<Key,Integer> actual=new SimpleHashMap<>(17);
        Map<Key,Integer> oracle=new HashMap<>();
        Random r=new Random(0x8AE2EF1FL);
        for(int i=0;i<5000;i++){
            Key k=new Key(r.nextInt(150),r.nextInt(9)-4);
            if(r.nextBoolean()){
                int v=r.nextInt(); actual.put(k,v); oracle.put(k,v);
            } else {
                eq(actual.get(k),oracle.get(k));
            }
        }
        for(Map.Entry<Key,Integer> e:oracle.entrySet()) eq(actual.get(e.getKey()),e.getValue());
        System.out.println("PASS collisions=pass update=pass negative-hash=pass random=5000 hashmap-oracle=pass null-contract=reject");
    }

    private static void eq(Object a,Object b){ if(!Objects.equals(a,b)) throw new AssertionError("actual="+a+" expected="+b); }
    private static void expect(Runnable r){ boolean ok=false; try{r.run();}catch(IllegalArgumentException|NullPointerException e){ok=true;} if(!ok) throw new AssertionError("expected rejection"); }
}
