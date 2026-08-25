import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class IterativeTraversalFixture {
    static void recursivePre(IterativeBinaryTreeTraversal.Node n,List<Integer> o){ if(n==null)return; o.add(n.value); recursivePre(n.left,o); recursivePre(n.right,o); }
    static void recursiveIn(IterativeBinaryTreeTraversal.Node n,List<Integer> o){ if(n==null)return; recursiveIn(n.left,o); o.add(n.value); recursiveIn(n.right,o); }
    static void recursivePost(IterativeBinaryTreeTraversal.Node n,List<Integer> o){ if(n==null)return; recursivePost(n.left,o); recursivePost(n.right,o); o.add(n.value); }
    static List<Integer> pre(IterativeBinaryTreeTraversal.Node n){ List<Integer> o=new ArrayList<>();recursivePre(n,o);return o; }
    static List<Integer> in(IterativeBinaryTreeTraversal.Node n){ List<Integer> o=new ArrayList<>();recursiveIn(n,o);return o; }
    static List<Integer> post(IterativeBinaryTreeTraversal.Node n){ List<Integer> o=new ArrayList<>();recursivePost(n,o);return o; }

    static IterativeBinaryTreeTraversal.Node randomTree(Random r,int depth,int[] seq){
        if(depth==0 || r.nextInt(5)==0) return null;
        IterativeBinaryTreeTraversal.Node n=new IterativeBinaryTreeTraversal.Node(seq[0]++);
        n.left=randomTree(r,depth-1,seq); n.right=randomTree(r,depth-1,seq); return n;
    }
    static void check(IterativeBinaryTreeTraversal.Node root){
        if(!IterativeBinaryTreeTraversal.preorder(root).equals(pre(root))) throw new AssertionError("preorder");
        if(!IterativeBinaryTreeTraversal.inorder(root).equals(in(root))) throw new AssertionError("inorder");
        if(!IterativeBinaryTreeTraversal.postorder(root).equals(post(root))) throw new AssertionError("postorder");
    }
    public static void main(String[] args){
        check(null);
        IterativeBinaryTreeTraversal.Node root=new IterativeBinaryTreeTraversal.Node(1);
        root.left=new IterativeBinaryTreeTraversal.Node(2); root.right=new IterativeBinaryTreeTraversal.Node(3);
        root.left.left=new IterativeBinaryTreeTraversal.Node(4); root.left.right=new IterativeBinaryTreeTraversal.Node(5);
        check(root);
        Random r=new Random(0x720d2901L);
        for(int t=0;t<1200;t++) check(randomTree(r,9,new int[]{0}));
        IterativeBinaryTreeTraversal.Node deep=new IterativeBinaryTreeTraversal.Node(0), cur=deep;
        for(int i=1;i<20000;i++){cur.right=new IterativeBinaryTreeTraversal.Node(i);cur=cur.right;}
        List<Integer> a=IterativeBinaryTreeTraversal.preorder(deep), b=IterativeBinaryTreeTraversal.inorder(deep), c=IterativeBinaryTreeTraversal.postorder(deep);
        if(a.size()!=20000||b.size()!=20000||c.size()!=20000) throw new AssertionError("deep-size");
        for(int i=0;i<20000;i++){ if(a.get(i)!=i||b.get(i)!=i||c.get(i)!=(19999-i)) throw new AssertionError("deep-order@"+i); }
        System.out.println("PASS fixed-tree randomized=1200 recursive-oracle deep-right-chain=20000 preorder-inorder-postorder");
    }
}
