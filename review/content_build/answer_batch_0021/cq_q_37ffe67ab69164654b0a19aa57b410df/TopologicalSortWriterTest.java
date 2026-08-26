import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class TopologicalSortWriterTest {
    private static long exhaustiveGraphs = 0;

    public static void main(String[] args) {
        for (int n = 0; n <= 4; n++) enumerateSimpleGraphs(n);
        check(new int[][]{{0,2},{1,2},{2,3}}, 4);
        check(new int[][]{{0,1},{0,1},{1,2}}, 3);
        expectCycle(1, new int[][]{{0,0}});
        expectCycle(3, new int[][]{{0,1},{1,2},{2,0}});
        Random r = new Random(20260826L);
        for (int rep = 0; rep < 500; rep++) {
            int n = 1 + r.nextInt(40);
            List<int[]> es = new ArrayList<>();
            for (int u = 0; u < n; u++) for (int v = u + 1; v < n; v++) if (r.nextInt(11) == 0) es.add(new int[]{u,v});
            check(es.toArray(int[][]::new), n);
        }
        expect(IllegalArgumentException.class, () -> TopologicalSort.sort(-1, new int[0][]));
        expect(NullPointerException.class, () -> TopologicalSort.sort(0, null));
        expect(IllegalArgumentException.class, () -> TopologicalSort.sort(2, new int[][]{{0}}));
        expect(IllegalArgumentException.class, () -> TopologicalSort.sort(2, new int[][]{{0,2}}));
        System.out.printf("PASS exhaustive_simple_graphs=%d random_dags=500 duplicate_edges=pass cycles=pass invalid=reject%n", exhaustiveGraphs);
    }

    private static void enumerateSimpleGraphs(int n) {
        List<int[]> possible = new ArrayList<>();
        for (int u = 0; u < n; u++) for (int v = 0; v < n; v++) if (u != v) possible.add(new int[]{u,v});
        int count = 1 << possible.size();
        for (int mask = 0; mask < count; mask++) {
            List<int[]> es = new ArrayList<>();
            for (int i = 0; i < possible.size(); i++) if ((mask & (1 << i)) != 0) es.add(possible.get(i));
            int[][] edges = es.toArray(int[][]::new);
            boolean cycle = hasCycle(n, edges);
            if (cycle) expectCycle(n, edges); else check(edges, n);
            exhaustiveGraphs++;
        }
    }

    private static boolean hasCycle(int n, int[][] edges) {
        List<List<Integer>> g = new ArrayList<>();
        for (int i = 0; i < n; i++) g.add(new ArrayList<>());
        for (int[] e : edges) g.get(e[0]).add(e[1]);
        int[] state = new int[n];
        for (int v = 0; v < n; v++) if (state[v] == 0 && dfs(v, g, state)) return true;
        return false;
    }

    private static boolean dfs(int v, List<List<Integer>> g, int[] state) {
        state[v] = 1;
        for (int w : g.get(v)) {
            if (state[w] == 1) return true;
            if (state[w] == 0 && dfs(w, g, state)) return true;
        }
        state[v] = 2;
        return false;
    }

    private static void check(int[][] edges, int n) {
        int[] order = TopologicalSort.sort(n, edges);
        if (order.length != n) throw new AssertionError("wrong length");
        int[] pos = new int[n];
        boolean[] seen = new boolean[n];
        for (int i = 0; i < n; i++) {
            int v = order[i];
            if (v < 0 || v >= n || seen[v]) throw new AssertionError("invalid vertex order=" + Arrays.toString(order));
            seen[v] = true; pos[v] = i;
        }
        for (int[] e : edges) if (pos[e[0]] >= pos[e[1]]) throw new AssertionError("edge order violation " + Arrays.toString(e));
    }

    private static void expectCycle(int n, int[][] edges) {
        expect(IllegalArgumentException.class, () -> TopologicalSort.sort(n, edges));
    }

    private static void expect(Class<? extends Throwable> type, Runnable action) {
        try { action.run(); throw new AssertionError("missing " + type.getSimpleName()); }
        catch (Throwable t) { if (!type.isInstance(t)) throw new AssertionError("wrong exception " + t); }
    }
}
