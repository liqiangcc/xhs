import java.util.List;

public final class DoublyLinkedListTest {
    private static void eq(Object actual,Object expected,String name){
        if(!actual.equals(expected)) throw new AssertionError(name+": "+actual+" != "+expected);
    }
    private static void yes(boolean value,String name){if(!value)throw new AssertionError(name);}
    public static void main(String[] args){
        DoublyLinkedList a=new DoublyLinkedList();
        eq(a.size(),0,"empty-size");
        eq(a.valuesForward(),List.of(),"empty-forward");
        eq(a.valuesBackward(),List.of(),"empty-backward");
        DoublyLinkedList.Node n2=a.addFirst(2);
        a.addFirst(1);
        DoublyLinkedList.Node n4=a.addLast(4);
        DoublyLinkedList.Node n3=a.insertAfter(n2,3);
        eq(a.valuesForward(),List.of(1,2,3,4),"forward");
        eq(a.valuesBackward(),List.of(4,3,2,1),"backward");
        eq(a.size(),4,"size");
        a.insertAfter(n4,5);
        eq(a.valuesForward(),List.of(1,2,3,4,5),"tail-via-anchor");
        eq(a.valuesBackward(),List.of(5,4,3,2,1),"tail-backward");
        yes(n3.value()==3,"returned-node");
        DoublyLinkedList b=new DoublyLinkedList();
        DoublyLinkedList.Node foreign=b.addFirst(9);
        boolean rejected=false;try{a.insertAfter(foreign,8);}catch(IllegalArgumentException e){rejected=true;}
        yes(rejected,"foreign-anchor-rejected");
        boolean nullRejected=false;try{a.insertAfter(null,8);}catch(IllegalArgumentException e){nullRejected=true;}
        yes(nullRejected,"null-anchor-rejected");
        System.out.println("PASS empty=true first=true last=true middle=true forward=1,2,3,4,5 backward=5,4,3,2,1 foreign-anchor=rejected null-anchor=rejected");
    }
}
