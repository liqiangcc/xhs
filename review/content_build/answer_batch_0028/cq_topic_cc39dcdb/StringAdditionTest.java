import java.math.BigInteger;
public final class StringAdditionTest {
    static void eq(String e,String a,String n){if(!e.equals(a))throw new AssertionError(n+" expected="+e+" actual="+a);}
    static String oracle(String s){return s.isEmpty()?"0":s;}
    static void enumerate(String prefix,int left,java.util.List<String> out){if(left==0){out.add(prefix);return;}for(char c='0';c<='3';c++)enumerate(prefix+c,left-1,out);}
    public static void main(String[] args){
        eq("321",StringAddition.add("321",""),"right-empty");eq("321",StringAddition.add("","321"),"left-empty");eq("0",StringAddition.add("",""),"both-empty");eq("10",StringAddition.add("9","1"),"carry");eq("0",StringAddition.add("000","00"),"leading-zero");
        var vals=new java.util.ArrayList<String>(); vals.add("");for(int n=1;n<=3;n++)enumerate("",n,vals);int checked=0;
        for(String a:vals)for(String b:vals){String e=new BigInteger(oracle(a)).add(new BigInteger(oracle(b))).toString();eq(e,StringAddition.add(a,b),"oracle");checked++;}
        try{StringAddition.add(null,"1");throw new AssertionError("null accepted");}catch(IllegalArgumentException expected){}try{StringAddition.add("1x","2");throw new AssertionError("nondigit accepted");}catch(IllegalArgumentException expected){}
        System.out.println("PASS empty-as-zero=verified leading-zero=normalized carry=verified oracle-pairs="+checked+" invalid-input=rejected");
    }
}
