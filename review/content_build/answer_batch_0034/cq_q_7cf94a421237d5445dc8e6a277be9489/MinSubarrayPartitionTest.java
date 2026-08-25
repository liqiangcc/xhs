public final class MinSubarrayPartitionTest {
    private static void eq(int actual,int expected,String name){if(actual!=expected)throw new AssertionError(name+" expected="+expected+" actual="+actual);}
    public static void main(String[] args){
        eq(MinSubarrayPartition.minSegments(new int[]{},3),0,"empty");
        eq(MinSubarrayPartition.minSegments(new int[]{1,2,3},3),2,"basic");
        eq(MinSubarrayPartition.minSegments(new int[]{6,-2},5),1,"positive rescued by negative");
        eq(MinSubarrayPartition.minSegments(new int[]{5},4),-1,"impossible singleton");
        eq(MinSubarrayPartition.minSegments(new int[]{2,-5,7},4),1,"whole signed segment");
        eq(MinSubarrayPartition.minSegments(new int[]{4,4,4},4),3,"exact boundaries");
        eq(MinSubarrayPartition.minSegments(new int[]{Integer.MAX_VALUE,Integer.MAX_VALUE},Long.MAX_VALUE),1,"long prefix");
        System.out.println("PASS empty basic signed-rescue impossible signed-whole exact-boundary long-prefix");
    }
}
