import java.util.*;
public final class LcpWriterTest {
    static String oracle(String[] a) {
        if (a.length == 0) return "";
        int k=0;
        outer: while (true) {
            Character c=null;
            for (String s:a) {
                if (k>=s.length()) break outer;
                if (c==null) c=s.charAt(k); else if (s.charAt(k)!=c) break outer;
            }
            k++;
        }
        return a[0].substring(0,k);
    }
    static void enumerateWords(List<String> words,String prefix,int depth){
        words.add(prefix);
        if(depth==3)return;
        for(char c:new char[]{'a','b','c'}) enumerateWords(words,prefix+c,depth+1);
    }
    public static void main(String[] args){
        Solution s=new Solution();
        Map<String[],String> known=new LinkedHashMap<>();
        known.put(new String[]{"flower","flow","flight"},"fl");
        known.put(new String[]{"dog","racecar","car"},"");
        known.put(new String[]{"","abc"},"");
        known.put(new String[]{"same"},"same");
        for(var e:known.entrySet()) if(!s.longestCommonPrefix(e.getKey()).equals(e.getValue())) throw new AssertionError();
        List<String> words=new ArrayList<>(); enumerateWords(words,"",0);
        for(String a:words) for(String b:words) for(String c:words){
            String[] in={a,b,c}; String got=s.longestCommonPrefix(in),want=oracle(in);
            if(!got.equals(want)) throw new AssertionError(Arrays.toString(in)+" got="+got+" want="+want);
        }
        if(!s.longestCommonPrefix(new String[0]).equals("")) throw new AssertionError();
        try{s.longestCommonPrefix(null);throw new AssertionError();}catch(IllegalArgumentException ok){}
        try{s.longestCommonPrefix(new String[]{"a",null});throw new AssertionError();}catch(IllegalArgumentException ok){}
        System.out.println("PASS known-cases exhaustive-3word-alphabet-abc-depth-3 independent-oracle empty-array null-rejected");
    }
}
