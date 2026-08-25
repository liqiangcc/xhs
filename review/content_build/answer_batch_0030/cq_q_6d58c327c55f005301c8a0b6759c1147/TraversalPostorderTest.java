import java.util.*;

public final class TraversalPostorderTest {
    static final class Node { int v; Node l,r; Node(int v,Node l,Node r){this.v=v;this.l=l;this.r=r;} }
    static int shapeCount = 0;

    public static void main(String[] args) {
        eq(new int[]{4,5,2,3,1}, TraversalPostorder.toPostorder(new int[]{1,2,4,5,3}, new int[]{4,2,5,1,3}), "example");
        eq(new int[]{}, TraversalPostorder.toPostorder(new int[]{}, new int[]{}), "empty");
        eq(new int[]{7}, TraversalPostorder.toPostorder(new int[]{7}, new int[]{7}), "single");
        for (int n=0;n<=8;n++) for (Node tree : shapes(n)) {
            assignPreorderIds(tree, new int[]{1});
            int[] pre=preorder(tree), in=inorder(tree), post=postorder(tree);
            eq(post, TraversalPostorder.toPostorder(pre,in), "shape n="+n+" pre="+Arrays.toString(pre)+" in="+Arrays.toString(in));
            shapeCount++;
        }
        throwsIAE(() -> TraversalPostorder.toPostorder(new int[]{1,1,2}, new int[]{1,1,2}), "duplicate ambiguity");
        throwsIAE(() -> TraversalPostorder.toPostorder(new int[]{1,2}, new int[]{1,3}), "set mismatch");
        throwsIAE(() -> TraversalPostorder.toPostorder(new int[]{1,2,3}, new int[]{3,1,2}), "structural inconsistency");
        throwsIAE(() -> TraversalPostorder.toPostorder(new int[]{1}, new int[]{}), "length mismatch");
        System.out.println("PASS example=yes all-shapes-n0..8="+shapeCount+" duplicate-rejected=yes invalid-set-rejected=yes inconsistent-order-rejected=yes");
    }

    static List<Node> shapes(int n) {
        if (n==0) return Collections.singletonList(null);
        List<Node> out=new ArrayList<>();
        for(int left=0;left<n;left++) {
            int right=n-1-left;
            for(Node l:shapes(left)) for(Node r:shapes(right)) out.add(new Node(0,copy(l),copy(r)));
        }
        return out;
    }
    static Node copy(Node x){return x==null?null:new Node(x.v,copy(x.l),copy(x.r));}
    static void assignPreorderIds(Node x,int[] next){if(x==null)return;x.v=next[0]++;assignPreorderIds(x.l,next);assignPreorderIds(x.r,next);}
    static int[] preorder(Node x){List<Integer>a=new ArrayList<>();pre(x,a);return a.stream().mapToInt(Integer::intValue).toArray();}
    static int[] inorder(Node x){List<Integer>a=new ArrayList<>();in(x,a);return a.stream().mapToInt(Integer::intValue).toArray();}
    static int[] postorder(Node x){List<Integer>a=new ArrayList<>();post(x,a);return a.stream().mapToInt(Integer::intValue).toArray();}
    static void pre(Node x,List<Integer>a){if(x==null)return;a.add(x.v);pre(x.l,a);pre(x.r,a);}
    static void in(Node x,List<Integer>a){if(x==null)return;in(x.l,a);a.add(x.v);in(x.r,a);}
    static void post(Node x,List<Integer>a){if(x==null)return;post(x.l,a);post(x.r,a);a.add(x.v);}
    static void eq(int[] e,int[] a,String label){if(!Arrays.equals(e,a))throw new AssertionError(label+" expected="+Arrays.toString(e)+" actual="+Arrays.toString(a));}
    static void throwsIAE(Runnable r,String label){try{r.run();throw new AssertionError(label+" did not reject");}catch(IllegalArgumentException expected){}}
}
