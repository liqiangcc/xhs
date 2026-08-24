import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

public final class GraphCloneTest {
    private static int fixed = 0;

    public static void main(String[] args) {
        fixedCases();
        randomizedCases();
        System.out.println("PASS fixed=" + fixed + " randomized=3000 oracle=paired-bijection sharedNodes=0 mutation=none");
    }

    private static void fixedCases() {
        check(null); // 1
        check(new GraphClone.Node(1)); // 2

        GraphClone.Node a = new GraphClone.Node(1);
        GraphClone.Node b = new GraphClone.Node(2);
        link(a, b);
        check(a); // 3

        GraphClone.Node c1 = new GraphClone.Node(1);
        GraphClone.Node c2 = new GraphClone.Node(2);
        GraphClone.Node c3 = new GraphClone.Node(3);
        link(c1, c2); link(c2, c3); link(c3, c1);
        check(c1); // 4

        GraphClone.Node self = new GraphClone.Node(7);
        self.neighbors.add(self);
        check(self); // 5

        GraphClone.Node d1 = new GraphClone.Node(5);
        GraphClone.Node d2 = new GraphClone.Node(5);
        GraphClone.Node d3 = new GraphClone.Node(5);
        link(d1, d2); link(d1, d3); link(d2, d3);
        check(d1); // 6 duplicate values

        GraphClone.Node p1 = new GraphClone.Node(9);
        GraphClone.Node p2 = new GraphClone.Node(9);
        p1.neighbors.add(p2);
        p1.neighbors.add(p2);
        p2.neighbors.add(p1);
        p2.neighbors.add(p1);
        check(p1); // 7 parallel adjacency entries
    }

    private static void randomizedCases() {
        Random random = new Random(0xC10E6A7L);
        for (int round = 0; round < 3000; round++) {
            int n = 1 + random.nextInt(12);
            List<GraphClone.Node> nodes = new ArrayList<>();
            for (int i = 0; i < n; i++) {
                nodes.add(new GraphClone.Node(random.nextInt(5) - 2));
            }
            for (int i = 1; i < n; i++) {
                link(nodes.get(i), nodes.get(random.nextInt(i)));
            }
            int extra = random.nextInt(n * 3 + 1);
            for (int i = 0; i < extra; i++) {
                GraphClone.Node x = nodes.get(random.nextInt(n));
                GraphClone.Node y = nodes.get(random.nextInt(n));
                link(x, y);
                if (random.nextDouble() < 0.15) {
                    link(x, y); // preserve duplicate adjacency entries too
                }
            }
            checkRandom(nodes.get(0), round);
        }
    }

    private static void check(GraphClone.Node start) {
        fixed++;
        String before = serialize(start);
        GraphClone.Node clone = GraphClone.cloneGraph(start);
        verifyEquivalentDeepClone(start, clone);
        if (!before.equals(serialize(start))) {
            throw new AssertionError("fixed case " + fixed + " mutated original graph");
        }
    }

    private static void checkRandom(GraphClone.Node start, int round) {
        String before = serialize(start);
        GraphClone.Node clone = GraphClone.cloneGraph(start);
        verifyEquivalentDeepClone(start, clone);
        if (!before.equals(serialize(start))) {
            throw new AssertionError("random case " + round + " mutated original graph");
        }
    }

    private static void verifyEquivalentDeepClone(GraphClone.Node original, GraphClone.Node clone) {
        if (original == null || clone == null) {
            if (original != clone) {
                throw new AssertionError("null contract mismatch");
            }
            return;
        }

        Map<GraphClone.Node, GraphClone.Node> forward = new IdentityHashMap<>();
        Map<GraphClone.Node, GraphClone.Node> reverse = new IdentityHashMap<>();
        Set<GraphClone.Node> originals = java.util.Collections.newSetFromMap(new IdentityHashMap<>());
        collect(original, originals);

        Deque<Pair> queue = new ArrayDeque<>();
        forward.put(original, clone);
        reverse.put(clone, original);
        queue.addLast(new Pair(original, clone));

        while (!queue.isEmpty()) {
            Pair pair = queue.removeFirst();
            GraphClone.Node a = pair.original;
            GraphClone.Node b = pair.copy;
            if (a == b || originals.contains(b)) {
                throw new AssertionError("clone shares original node identity");
            }
            if (a.value != b.value || a.neighbors.size() != b.neighbors.size()) {
                throw new AssertionError("node value or adjacency size mismatch");
            }
            for (int i = 0; i < a.neighbors.size(); i++) {
                GraphClone.Node an = a.neighbors.get(i);
                GraphClone.Node bn = b.neighbors.get(i);
                GraphClone.Node mapped = forward.get(an);
                if (mapped == null) {
                    GraphClone.Node reverseMapped = reverse.get(bn);
                    if (reverseMapped != null && reverseMapped != an) {
                        throw new AssertionError("clone mapping is not bijective");
                    }
                    forward.put(an, bn);
                    reverse.put(bn, an);
                    queue.addLast(new Pair(an, bn));
                } else if (mapped != bn) {
                    throw new AssertionError("adjacency target mapping mismatch");
                }
            }
        }
        if (forward.size() != originals.size() || reverse.size() != originals.size()) {
            throw new AssertionError("reachable node count mismatch");
        }
    }

    private static void collect(GraphClone.Node start, Set<GraphClone.Node> out) {
        if (start == null) return;
        Deque<GraphClone.Node> queue = new ArrayDeque<>();
        out.add(start);
        queue.addLast(start);
        while (!queue.isEmpty()) {
            GraphClone.Node node = queue.removeFirst();
            for (GraphClone.Node neighbor : node.neighbors) {
                if (out.add(neighbor)) queue.addLast(neighbor);
            }
        }
    }

    private static void link(GraphClone.Node a, GraphClone.Node b) {
        a.neighbors.add(b);
        b.neighbors.add(a);
    }

    private static String serialize(GraphClone.Node start) {
        if (start == null) return "#";
        Map<GraphClone.Node, Integer> ids = new IdentityHashMap<>();
        List<GraphClone.Node> order = new ArrayList<>();
        Deque<GraphClone.Node> queue = new ArrayDeque<>();
        ids.put(start, 0);
        order.add(start);
        queue.addLast(start);
        while (!queue.isEmpty()) {
            GraphClone.Node node = queue.removeFirst();
            for (GraphClone.Node neighbor : node.neighbors) {
                if (!ids.containsKey(neighbor)) {
                    ids.put(neighbor, ids.size());
                    order.add(neighbor);
                    queue.addLast(neighbor);
                }
            }
        }
        StringBuilder sb = new StringBuilder();
        for (GraphClone.Node node : order) {
            sb.append(ids.get(node)).append(':').append(node.value).append("->[");
            for (GraphClone.Node neighbor : node.neighbors) {
                sb.append(ids.get(neighbor)).append(',');
            }
            sb.append("];\n");
        }
        return sb.toString();
    }

    private record Pair(GraphClone.Node original, GraphClone.Node copy) {}
}
