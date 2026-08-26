import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

public final class TopologicalSort {
    private TopologicalSort() {}

    public static int[] sort(int vertexCount, int[][] edges) {
        if (vertexCount < 0) throw new IllegalArgumentException("vertexCount must be >= 0");
        if (edges == null) throw new NullPointerException("edges");
        List<List<Integer>> graph = new ArrayList<>(vertexCount);
        for (int i = 0; i < vertexCount; i++) graph.add(new ArrayList<>());
        int[] indegree = new int[vertexCount];
        for (int[] edge : edges) {
            if (edge == null || edge.length != 2) throw new IllegalArgumentException("each edge must contain from and to");
            int from = edge[0], to = edge[1];
            if (from < 0 || from >= vertexCount || to < 0 || to >= vertexCount) throw new IllegalArgumentException("edge endpoint out of range");
            graph.get(from).add(to);
            indegree[to]++;
        }
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        for (int v = 0; v < vertexCount; v++) if (indegree[v] == 0) queue.addLast(v);
        int[] order = new int[vertexCount];
        int size = 0;
        while (!queue.isEmpty()) {
            int v = queue.removeFirst();
            order[size++] = v;
            for (int next : graph.get(v)) if (--indegree[next] == 0) queue.addLast(next);
        }
        if (size != vertexCount) throw new IllegalArgumentException("graph contains a directed cycle");
        return order;
    }
}
