public final class MaxRootToLeafCost {
    public static final class Node { final long cost; Node left; Node right; Node(long cost){this.cost=cost;} }
    public static long maxCost(Node root){ return root==null?0L:dfs(root); }
    private static long dfs(Node node){
        if(node.left==null && node.right==null) return node.cost;
        if(node.left==null) return node.cost+dfs(node.right);
        if(node.right==null) return node.cost+dfs(node.left);
        return node.cost+Math.max(dfs(node.left),dfs(node.right));
    }
}
