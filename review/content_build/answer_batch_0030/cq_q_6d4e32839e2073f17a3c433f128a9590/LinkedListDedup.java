import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public final class LinkedListDedup {
    public static final class ListNode {
        int val; ListNode next;
        ListNode(int val) { this.val = val; }
    }
    public static ListNode keepOneSorted(ListNode head) {
        for (ListNode cur=head; cur!=null && cur.next!=null; ) {
            if (cur.val==cur.next.val) cur.next=cur.next.next; else cur=cur.next;
        }
        return head;
    }
    public static ListNode removeAllDuplicatesSorted(ListNode head) {
        ListNode dummy=new ListNode(0); dummy.next=head; ListNode prev=dummy,cur=head;
        while(cur!=null){
            if(cur.next!=null && cur.val==cur.next.val){int duplicate=cur.val;while(cur!=null&&cur.val==duplicate)cur=cur.next;prev.next=cur;}
            else {prev=cur;cur=cur.next;}
        }
        return dummy.next;
    }
    public static ListNode keepFirstUnsorted(ListNode head) {
        Set<Integer> seen=new HashSet<>(); ListNode dummy=new ListNode(0); dummy.next=head; ListNode prev=dummy,cur=head;
        while(cur!=null){if(!seen.add(cur.val))prev.next=cur.next;else prev=cur;cur=cur.next;} return dummy.next;
    }
    public static ListNode keepOnlyGloballyUniqueUnsorted(ListNode head) {
        Map<Integer,Integer> freq=new HashMap<>(); for(ListNode cur=head;cur!=null;cur=cur.next)freq.merge(cur.val,1,Integer::sum);
        ListNode dummy=new ListNode(0),tail=dummy; for(ListNode cur=head;cur!=null;){ListNode next=cur.next;if(freq.get(cur.val)==1){tail.next=cur;tail=cur;}cur=next;} tail.next=null; return dummy.next;
    }
    static ListNode from(int[] a){ListNode d=new ListNode(0),t=d;for(int v:a){t.next=new ListNode(v);t=t.next;}return d.next;}
    static int[] toArray(ListNode h){int n=0;for(ListNode c=h;c!=null;c=c.next)n++;int[] a=new int[n];int i=0;for(ListNode c=h;c!=null;c=c.next)a[i++]=c.val;return a;}
}
