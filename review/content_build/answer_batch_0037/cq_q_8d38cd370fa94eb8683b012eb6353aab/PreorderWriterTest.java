import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class PreorderWriterTest {
    private static int randomCases;
    public static void main(String[] args) {
        Solution s=new Solution();
        check(s,null,List.of());
        check(s,node(7),List.of(7));
        Solution.TreeNode sample=node(1); sample.right=node(2); sample.right.left=node(3);
        check(s,sample,List.of(1,2,3));
        Solution.TreeNode full=node(1); full.left=node(2); full.right=node(3); full.left.left=node(4); full.left.right=node(5); full.right.left=node(6); full.right.right=node(7);
        check(s,full,List.of(1,2,4,5,3,6,7));
        Random r=new Random(0x8D38CD37L);
        for(int n=0;n<=120;n++) for(int round=0;round<20;round++) { Solution.TreeNode root=randomTree(n,r); check(s,root,reference(root)); randomCases++; }
        int depth=50000; Solution.TreeNode skew=node(0),cur=skew; for(int i=1;i<depth;i++){cur.right=node(i);cur=cur.right;}
        List<Integer> got=s.preorderTraversal(skew); if(got.size()!=depth||got.get(0)!=0||got.get(depth-1)!=depth-1) throw new AssertionError("deep skew mismatch");
        System.out.printf("PASS fixed=4 randomized_trees=%d deep_skew=%d null=pass order=pass%n",randomCases,depth);
    }
    static Solution.TreeNode node(int v){return new Solution.TreeNode(v);}
    static void check(Solution s,Solution.TreeNode root,List<Integer> expected){List<Integer> actual=s.preorderTraversal(root);if(!actual.equals(expected))throw new AssertionError("actual="+actual+" expected="+expected);}
    static List<Integer> reference(Solution.TreeNode root){List<Integer> out=new ArrayList<>();ref(root,out);return out;}
    static void ref(Solution.TreeNode n,List<Integer> out){if(n==null)return;out.add(n.val);ref(n.left,out);ref(n.right,out);}
    static Solution.TreeNode randomTree(int n,Random r){if(n==0)return null;List<Solution.TreeNode> nodes=new ArrayList<>();for(int i=0;i<n;i++)nodes.add(node(r.nextInt(2001)-1000));List<Solution.TreeNode> open=new ArrayList<>();open.add(nodes.get(0));for(int i=1;i<n;i++){Solution.TreeNode child=nodes.get(i);while(true){Solution.TreeNode p=open.get(r.nextInt(open.size()));if(p.left!=null&&p.right!=null){open.remove(p);continue;}if(p.left==null&&p.right==null){if(r.nextBoolean())p.left=child;else p.right=child;}else if(p.left==null)p.left=child;else p.right=child;if(p.left!=null&&p.right!=null)open.remove(p);open.add(child);break;}}return nodes.get(0);}
}
