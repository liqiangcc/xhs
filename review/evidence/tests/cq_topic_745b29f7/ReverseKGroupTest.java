public final class ReverseKGroupTest {
    static ReverseKGroup.ListNode list(int... v) { ReverseKGroup.ListNode d=new ReverseKGroup.ListNode(0),t=d; for(int x:v){t.next=new ReverseKGroup.ListNode(x);t=t.next;} return d.next; }
    static String text(ReverseKGroup.ListNode n) { StringBuilder s=new StringBuilder(); while(n!=null){if(s.length()>0)s.append(',');s.append(n.value);n=n.next;} return s.toString(); }
    static void require(String actual,String expected){if(!actual.equals(expected))throw new AssertionError(actual);}
    public static void main(String[] args) {
        require(text(ReverseKGroup.reverseKGroup(list(1,2,3,4,5),2)),"2,1,4,3,5");
        require(text(ReverseKGroup.reverseKGroup(list(1,2,3,4,5),3)),"3,2,1,4,5");
        require(text(ReverseKGroup.reverseKGroup(list(1,2,3),3)),"3,2,1");
        require(text(ReverseKGroup.reverseKGroup(list(1,2),3)),"1,2");
        require(text(ReverseKGroup.reverseKGroup(list(1,2,3),1)),"1,2,3");
        if(ReverseKGroup.reverseKGroup(null,2)!=null)throw new AssertionError("null");
        try { ReverseKGroup.reverseKGroup(list(1),0); throw new AssertionError("missing error"); } catch (IllegalArgumentException expected) { }
        try { ReverseKGroup.reverseKGroup(list(1),-1); throw new AssertionError("missing error"); } catch (IllegalArgumentException expected) { }
    }
}
