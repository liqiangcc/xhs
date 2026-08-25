public final class LinkedListIntersectionTest {
    private static void same(Object actual, Object expected, String name) {
        if (actual != expected) throw new AssertionError(name + " expected identity=" + expected + " actual=" + actual);
    }
    private static LinkedListIntersection.Node n(int v) { return new LinkedListIntersection.Node(v); }

    public static void main(String[] args) {
        var c1=n(7); var c2=n(8); c1.next=c2;
        var a1=n(1); var a2=n(2); a1.next=a2; a2.next=c1;
        var b1=n(3); var b2=n(4); var b3=n(5); b1.next=b2; b2.next=b3; b3.next=c1;
        same(LinkedListIntersection.firstIntersection(a1,b1),c1,"ordinary shared suffix");
        if(a1.next!=a2||a2.next!=c1||b1.next!=b2||b2.next!=b3||b3.next!=c1||c1.next!=c2) throw new AssertionError("input mutated");

        var sameHead=n(11); sameHead.next=n(12);
        same(LinkedListIntersection.firstIntersection(sameHead,sameHead),sameHead,"same head");

        var tail=n(99); var x=n(1); x.next=tail; var y1=n(2); var y2=n(3); y1.next=y2; y2.next=tail;
        same(LinkedListIntersection.firstIntersection(x,y1),tail,"single shared tail node");

        var v1=n(1); v1.next=n(2); v1.next.next=n(3);
        var w1=n(1); w1.next=n(2); w1.next.next=n(3);
        same(LinkedListIntersection.firstIntersection(v1,w1),null,"equal values but distinct nodes");

        same(LinkedListIntersection.firstIntersection(null,v1),null,"one empty");
        same(LinkedListIntersection.firstIntersection(null,null),null,"both empty");
        System.out.println("PASS shared-suffix same-head shared-tail identity-not-value empty-cases no-mutation");
    }
}
