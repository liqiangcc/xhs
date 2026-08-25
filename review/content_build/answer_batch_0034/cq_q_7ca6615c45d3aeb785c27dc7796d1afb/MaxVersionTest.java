import java.util.List;
public final class MaxVersionTest {
    static void eq(Object a,Object b,String n){if(!a.equals(b))throw new AssertionError(n+" expected="+b+" actual="+a);}
    static void cmp(String a,String b,int sign){int x=Integer.signum(MaxVersion.compareVersion(a,b));if(x!=sign)throw new AssertionError(a+" vs "+b+" got "+x);}
    static void bad(String s){try{MaxVersion.compareVersion(s,"1");throw new AssertionError("expected invalid "+s);}catch(IllegalArgumentException ok){}}
    public static void main(String[] args){
        cmp("1.2","1.10",-1); cmp("1.01","1.001",0); cmp("1.0","1.0.0.0",0); cmp("0.1","1.1",-1); cmp("1.0.1","1",1);
        cmp("2147483647.0000000000000000000000000001","2147483647.1",0);
        eq(MaxVersion.maxVersion(List.of("1.0.9","1.01.0","1.0.10","1.0.10.0")),"1.01.0","multiple max");
        eq(MaxVersion.maxVersion(List.of("2.0","2.0.0","1.999")),"2.0","equal-first");
        bad("1..0"); bad(".1"); bad("1."); bad("1.a");
        System.out.println("PASS lc165 examples leading-zero missing-zero long-revision multiple-input first-equal invalid-input");
    }
}
