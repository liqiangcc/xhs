import java.util.*;

public final class ThousandsSeparatorValidation {
    static String oracle(long value) {
        String s=Long.toString(value);
        int start=s.charAt(0)=='-'?1:0;
        String digits=s.substring(start);
        int first=digits.length()%3;
        if(first==0) first=3;
        StringBuilder out=new StringBuilder();
        if(start==1) out.append('-');
        out.append(digits,0,first);
        for(int i=first;i<digits.length();i+=3) out.append(',').append(digits,i,i+3);
        return out.toString();
    }
    static void check(long x, String expected) {
        String got=Solution.format(x);
        if(!got.equals(expected)) throw new AssertionError(x+" got="+got+" expected="+expected);
    }
    public static void main(String[] args) {
        check(0L,"0"); check(1L,"1"); check(999L,"999"); check(1000L,"1,000");
        check(1234567L,"1,234,567"); check(-1L,"-1"); check(-1000L,"-1,000");
        check(-1234567L,"-1,234,567"); check(Long.MAX_VALUE,"9,223,372,036,854,775,807");
        check(Long.MIN_VALUE,"-9,223,372,036,854,775,808");
        Random r=new Random(0x42A11CE5L);
        for(int i=0;i<20000;i++){
            long x=r.nextLong();
            String got=Solution.format(x), want=oracle(x);
            if(!got.equals(want)) throw new AssertionError("random x="+x+" got="+got+" want="+want);
        }
        System.out.println("PASS fixed=10 random=20000 positive+negative+zero+long-extremes=covered");
    }
}
