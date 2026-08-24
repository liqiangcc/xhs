public final class MaxRootToLeafCostTest {
    static void eq(long e,long a,String n){if(e!=a)throw new AssertionError(n+" expected="+e+" actual="+a);}
    public static void main(String[] args){
        eq(0,MaxRootToLeafCost.maxCost(null),"empty");
        eq(7,MaxRootToLeafCost.maxCost(new MaxRootToLeafCost.Node(7)),"single");
        var r=new MaxRootToLeafCost.Node(5); r.left=new MaxRootToLeafCost.Node(4); r.right=new MaxRootToLeafCost.Node(10); r.left.left=new MaxRootToLeafCost.Node(20); r.left.right=new MaxRootToLeafCost.Node(1); r.right.right=new MaxRootToLeafCost.Node(2); eq(29,MaxRootToLeafCost.maxCost(r),"balanced");
        var neg=new MaxRootToLeafCost.Node(-5); neg.left=new MaxRootToLeafCost.Node(-2); eq(-7,MaxRootToLeafCost.maxCost(neg),"negative-single-child");
        var mixed=new MaxRootToLeafCost.Node(-1); mixed.left=new MaxRootToLeafCost.Node(10); mixed.right=new MaxRootToLeafCost.Node(3); mixed.left.left=new MaxRootToLeafCost.Node(-20); mixed.right.right=new MaxRootToLeafCost.Node(4); eq(6,MaxRootToLeafCost.maxCost(mixed),"must-reach-leaf");
        System.out.println("PASS empty=0 single=7 balanced=29 negative-single-child=-7 must-reach-leaf=6");
    }
}
