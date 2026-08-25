import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class MaxAverageSubtreeReviewer {
    private static final double EPS = 1e-12;
    private static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
    private static void roots(MaxAverageSubtree.TreeNode n, List<MaxAverageSubtree.TreeNode> out) {
        if (n == null) return;
        out.add(n); roots(n.left, out); roots(n.right, out);
    }
    private static long[] aggregate(MaxAverageSubtree.TreeNode n) {
        if (n == null) return new long[]{0,0};
        long[] l=aggregate(n.left), r=aggregate(n.right);
        return new long[]{l[0]+r[0]+n.val,l[1]+r[1]+1};
    }
    private static double brute(MaxAverageSubtree.TreeNode root) {
        List<MaxAverageSubtree.TreeNode> rs=new ArrayList<>(); roots(root,rs);
        double best=Double.NEGATIVE_INFINITY;
        for (MaxAverageSubtree.TreeNode r:rs) { long[] a=aggregate(r); best=Math.max(best,(double)a[0]/a[1]); }
        return best;
    }
    private static MaxAverageSubtree.TreeNode randomTree(Random rnd,int n) {
        List<MaxAverageSubtree.TreeNode> a=new ArrayList<>();
        for(int i=0;i<n;i++) a.add(new MaxAverageSubtree.TreeNode(rnd.nextInt(2001)-1000));
        for(int i=1;i<n;i++) {
            while(true) {
                MaxAverageSubtree.TreeNode p=a.get(rnd.nextInt(i));
                if(p.left==null && p.right==null) { if(rnd.nextBoolean())p.left=a.get(i); else p.right=a.get(i); break; }
                if(p.left==null){p.left=a.get(i);break;} if(p.right==null){p.right=a.get(i);break;}
            }
        }
        return a.get(0);
    }
    public static void main(String[] args) {
        MaxAverageSubtree solver=new MaxAverageSubtree();
        MaxAverageSubtree.TreeNode chain=new MaxAverageSubtree.TreeNode(-10);
        chain.right=new MaxAverageSubtree.TreeNode(-20);
        chain.right.right=new MaxAverageSubtree.TreeNode(-3);
        check(Math.abs(solver.maxAverage(chain)-(-3.0))<EPS,"negative chain");
        Random rnd=new Random(17064238087L);
        for(int i=0;i<5000;i++) {
            MaxAverageSubtree.TreeNode t=randomTree(rnd,1+rnd.nextInt(25));
            double e=brute(t), a=solver.maxAverage(t);
            check(Math.abs(e-a)<EPS,"review oracle mismatch round="+i+" e="+e+" a="+a);
        }
        check(MaxAverageSubtree.greater(-1,3,-1,2),"negative exact fraction order");
        check(!MaxAverageSubtree.greater(1,3,2,6),"equal rational averages must not be greater");
        System.out.println("PASS reviewer-negative-chain=yes random-oracle=5000 exact-fractions=yes rooted-subtrees=enumerated");
    }
}
