import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public final class LinkedListEqualValueMatches {
    private LinkedListEqualValueMatches() {}

    public static final class Node {
        public final int value;
        public Node next;

        public Node(int value) {
            this.value = value;
        }
    }

    public record Match(int leftIndex, int rightIndex, int value) {}

    public static List<Match> findAll(Node leftHead, Node rightHead) {
        Map<Integer, List<Integer>> rightPositionsByValue = new HashMap<>();
        int rightIndex = 0;
        for (Node node = rightHead; node != null; node = node.next) {
            rightPositionsByValue
                    .computeIfAbsent(node.value, ignored -> new ArrayList<>())
                    .add(rightIndex++);
        }

        List<Match> matches = new ArrayList<>();
        int leftIndex = 0;
        for (Node node = leftHead; node != null; node = node.next) {
            List<Integer> rightPositions = rightPositionsByValue.get(node.value);
            if (rightPositions != null) {
                for (int position : rightPositions) {
                    matches.add(new Match(leftIndex, position, node.value));
                }
            }
            leftIndex++;
        }
        return List.copyOf(matches);
    }

    public static Node fromValues(int... values) {
        Objects.requireNonNull(values, "values");
        Node dummy = new Node(0);
        Node tail = dummy;
        for (int value : values) {
            tail.next = new Node(value);
            tail = tail.next;
        }
        return dummy.next;
    }
}
