import java.util.*;
public final class LinkedListDedupTest {
    public static void main(String[] args){
        eq(new int[]{1,2,3}, LinkedListDedup.toArray(LinkedListDedup.keepOneSorted(LinkedListDedup.from(new int[]{1,1,2,3,3}))), "sorted keep one");
        eq(new int[]{2}, LinkedListDedup.toArray(LinkedListDedup.removeAllDuplicatesSorted(LinkedListDedup.from(new int[]{1,1,2,3,3}))), "sorted remove all duplicates");
        eq(new int[]{3,1,2}, LinkedListDedup.toArray(LinkedListDedup.keepFirstUnsorted(LinkedListDedup.from(new int[]{3,1,3,2,1}))), "unsorted keep first");
        eq(new int[]{2,4}, LinkedListDedup.toArray(LinkedListDedup.keepOnlyGloballyUniqueUnsorted(LinkedListDedup.from(new int[]{3,1,3,2,1,4}))), "unsorted globally unique");
        exhaustive();
        System.out.println("PASS four-contract-examples=yes exhaustive-ternary-length7=yes empty=yes head-tail-duplicates=yes");
    }
    private static void exhaustive(){
        for(int n=0;n<=7;n++){
            int total=1;for(int i=0;i<n;i++)total*=3;
            for(int mask=0;mask<total;mask++){
                int[] a=new int[n];int x=mask;for(int i=0;i<n;i++){a[i]=x%3;x/=3;}
                int[] sorted=a.clone();Arrays.sort(sorted);
                eq(oracleKeepOne(sorted),LinkedListDedup.toArray(LinkedListDedup.keepOneSorted(LinkedListDedup.from(sorted))),"keepOne "+Arrays.toString(sorted));
                eq(oracleUniqueOnly(sorted),LinkedListDedup.toArray(LinkedListDedup.removeAllDuplicatesSorted(LinkedListDedup.from(sorted))),"removeAll sorted "+Arrays.toString(sorted));
                eq(oracleKeepFirst(a),LinkedListDedup.toArray(LinkedListDedup.keepFirstUnsorted(LinkedListDedup.from(a))),"keepFirst "+Arrays.toString(a));
                eq(oracleUniqueOnly(a),LinkedListDedup.toArray(LinkedListDedup.keepOnlyGloballyUniqueUnsorted(LinkedListDedup.from(a))),"unique unsorted "+Arrays.toString(a));
            }
        }
    }
    private static int[] oracleKeepOne(int[] a){LinkedHashSet<Integer>s=new LinkedHashSet<>();for(int v:a)s.add(v);return s.stream().mapToInt(Integer::intValue).toArray();}
    private static int[] oracleKeepFirst(int[] a){return oracleKeepOne(a);}
    private static int[] oracleUniqueOnly(int[] a){Map<Integer,Integer>f=new HashMap<>();for(int v:a)f.merge(v,1,Integer::sum);return Arrays.stream(a).filter(v->f.get(v)==1).toArray();}
    private static void eq(int[] e,int[] a,String label){if(!Arrays.equals(e,a))throw new AssertionError(label+" expected="+Arrays.toString(e)+" actual="+Arrays.toString(a));}
}
