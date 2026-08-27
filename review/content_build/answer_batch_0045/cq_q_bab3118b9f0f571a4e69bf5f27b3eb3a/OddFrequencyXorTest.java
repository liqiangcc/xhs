import java.util.*;
public final class OddFrequencyXorTest {
    static void check(int[] a,int expected){int got=OddFrequencyXor.findOddFrequency(a);if(got!=expected)throw new AssertionError(Arrays.toString(a)+" got="+got+" expected="+expected);}
    public static void main(String[] args){
        check(new int[]{7},7);check(new int[]{1,2,1},2);check(new int[]{-3,4,4,-3,-3},-3);check(new int[]{5,5,5,9,9,2,2},5);
        Random r=new Random(0xBAB3118BL);int random=0;
        for(int round=0;round<5000;round++){
            int target=r.nextInt();int targetPairs=r.nextInt(4);List<Integer> xs=new ArrayList<>();for(int i=0;i<2*targetPairs+1;i++)xs.add(target);
            int others=1+r.nextInt(8);Set<Integer> used=new HashSet<>();used.add(target);
            for(int j=0;j<others;j++){int v;do{v=r.nextInt();}while(!used.add(v));int pairs=1+r.nextInt(4);for(int k=0;k<2*pairs;k++)xs.add(v);}
            Collections.shuffle(xs,r);int[] a=xs.stream().mapToInt(Integer::intValue).toArray();check(a,target);random++;
        }
        try{OddFrequencyXor.findOddFrequency(null);throw new AssertionError("null accepted");}catch(IllegalArgumentException ok){}try{OddFrequencyXor.findOddFrequency(new int[0]);throw new AssertionError("empty accepted");}catch(IllegalArgumentException ok){}
        System.out.println("PASS fixed=4 random="+random+" negatives=pass arbitrary-even-counts=pass null-empty=rejected");
    }
}
