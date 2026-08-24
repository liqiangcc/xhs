import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

public final class GraphClone {
    private GraphClone() {}

    public static final class Node {
        public final int value;
        public final List<Node> neighbors = new ArrayList<>();

        public Node(int value) {
            this.value = value;
        }
    }

    public static Node cloneGraph(Node start) {
        if (start == null) {
            return null;
        }
        Map<Node, Node> clones = new IdentityHashMap<>();
        Deque<Node> queue = new ArrayDeque<>();
        clones.put(start, new Node(start.value));
        queue.addLast(start);

        while (!queue.isEmpty()) {
            Node original = queue.removeFirst();
            Node copy = clones.get(original);
            for (Node neighbor : original.neighbors) {
                Node neighborCopy = clones.get(neighbor);
                if (neighborCopy == null) {
                    neighborCopy = new Node(neighbor.value);
                    clones.put(neighbor, neighborCopy);
                    queue.addLast(neighbor);
                }
                copy.neighbors.add(neighborCopy);
            }
        }
        return clones.get(start);
    }
}
