import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

public final class DoublyLinkedListTest {
    private static Field field(Class<?> type, String name) throws Exception {
        Field f = type.getDeclaredField(name);
        f.setAccessible(true);
        return f;
    }

    private static List<Integer> values(DoublyLinkedList list, boolean forward) throws Exception {
        Field endpoint = field(DoublyLinkedList.class, forward ? "head" : "tail");
        Object node = endpoint.get(list);
        List<Integer> out = new ArrayList<>();
        while (node != null) {
            Class<?> nodeType = node.getClass();
            out.add((Integer) field(nodeType, "value").get(node));
            Object next = field(nodeType, forward ? "next" : "prev").get(node);
            if (next != null) {
                Object back = field(next.getClass(), forward ? "prev" : "next").get(next);
                if (back != node) {
                    throw new AssertionError("bidirectional adjacency broken");
                }
            }
            node = next;
        }
        return out;
    }

    private static void expect(List<Integer> expected, List<Integer> actual, String label) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    private static void expectInvalid(DoublyLinkedList list, int index) {
        try {
            list.insert(index, 99);
            throw new AssertionError("expected IndexOutOfBoundsException for index=" + index);
        } catch (IndexOutOfBoundsException expected) {
            // expected
        }
    }

    public static void main(String[] args) throws Exception {
        DoublyLinkedList list = new DoublyLinkedList();
        list.insert(0, 2);
        expect(List.of(2), values(list, true), "empty->first forward");
        expect(List.of(2), values(list, false), "empty->first reverse");

        list.insert(0, 1);
        list.insert(1, 9);
        list.insert(3, 3);
        expect(List.of(1, 9, 2, 3), values(list, true), "head-middle-tail forward");
        expect(List.of(3, 2, 9, 1), values(list, false), "head-middle-tail reverse");

        Object head = field(DoublyLinkedList.class, "head").get(list);
        Object tail = field(DoublyLinkedList.class, "tail").get(list);
        if (field(head.getClass(), "prev").get(head) != null) {
            throw new AssertionError("head.prev must be null");
        }
        if (field(tail.getClass(), "next").get(tail) != null) {
            throw new AssertionError("tail.next must be null");
        }
        if ((Integer) field(DoublyLinkedList.class, "size").get(list) != 4) {
            throw new AssertionError("size must be 4");
        }

        expectInvalid(list, -1);
        expectInvalid(list, 5);
        System.out.println("PASS empty=linked head=ok middle=ok tail=ok forward-reverse=consistent bounds=rejected size=4");
    }
}
