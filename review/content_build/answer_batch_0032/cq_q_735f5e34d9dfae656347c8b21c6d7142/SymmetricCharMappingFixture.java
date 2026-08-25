import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.Set;

public final class SymmetricCharMappingFixture {
    static boolean actual(String source,String target){
        Objects.requireNonNull(source);Objects.requireNonNull(target);
        int[] a=source.codePoints().toArray(),b=target.codePoints().toArray();
        if(a.length!=b.length)return false;
        Map<Integer,Integer> p=new HashMap<>();
        for(int i=0;i<a.length;i++){
            int x=a[i],y=b[i];Integer px=p.get(x),py=p.get(y);
            if(px!=null&&px!=y)return false;
            if(py!=null&&py!=x)return false;
            p.put(x,y);p.put(y,x);
        }
        return true;
    }
    static boolean relationOracle(String source,String target){
        int[] a=source.codePoints().toArray(),b=target.codePoints().toArray();
        if(a.length!=b.length)return false;
        Map<Integer,Set<Integer>> adjacent=new HashMap<>();
        for(int i=0;i<a.length;i++){
            adjacent.computeIfAbsent(a[i],k->new HashSet<>()).add(b[i]);
            adjacent.computeIfAbsent(b[i],k->new HashSet<>()).add(a[i]);
        }
        for(Set<Integer> neighbors:adjacent.values()) if(neighbors.size()!=1)return false;
        return true;
    }
    static String randomString(Random r,int n){
        int[] alphabet={'a','b','c','d','你',0x1F642},x=new int[n];
        for(int i=0;i<n;i++)x[i]=alphabet[r.nextInt(alphabet.length)];
        return new String(x,0,x.length);
    }
    static void check(String a,String b){
        boolean x=actual(a,b),y=relationOracle(a,b);
        if(x!=y)throw new AssertionError(a+" -> "+b+" actual="+x+" oracle="+y);
    }
    public static void main(String[] args){
        if(!actual("aabba","eeffe"))throw new AssertionError("source true example");
        if(actual("asdf","asag"))throw new AssertionError("source false example");
        check("aabba","eeffe");check("asdf","asag");check("","");check("aa","aa");check("ab","ba");
        check("🙂a🙂","你b你");check("🙂你","你🙂");
        if(actual("a","ab"))throw new AssertionError("length mismatch");
        Random r=new Random(735L);
        for(int t=0;t<20000;t++){int n=r.nextInt(12);check(randomString(r,n),randomString(r,n));}
        System.out.println("PASS source-examples unicode fixed-points randomized=20000 oracle=undirected-degree-one-relation");
    }
}
