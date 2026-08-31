import java.util.*;
public final class LongestCommonSubsequenceReviewerTest {
  private static final Random RNG = new Random(0x62006A7CL ^ 0x5A5A5A5AL);
  private static final char[] ALPHABET = {'a','b','c'};
  private static boolean isSubsequence(String candidate, String target) {
    int i=0; for(int j=0;j<target.length()&&i<candidate.length();j++) if(candidate.charAt(i)==target.charAt(j)) i++; return i==candidate.length();
  }
  private static int bruteOracle(String a, String b) {
    String shorter=a.length()<=b.length()?a:b, other=a.length()<=b.length()?b:a; int n=shorter.length(), best=0, masks=1<<n;
    for(int mask=0;mask<masks;mask++){int bits=Integer.bitCount(mask); if(bits<=best) continue; StringBuilder sb=new StringBuilder(bits); for(int i=0;i<n;i++) if((mask&(1<<i))!=0) sb.append(shorter.charAt(i)); if(isSubsequence(sb.toString(),other)) best=bits;} return best;
  }
  private static void check(String a,String b,int expected,String label){int actual=LongestCommonSubsequence.lcsLength(a,b); if(actual!=expected) throw new AssertionError(label+" expected="+expected+" actual="+actual+" a="+a+" b="+b); int reverse=LongestCommonSubsequence.lcsLength(b,a); if(reverse!=expected) throw new AssertionError(label+" symmetry expected="+expected+" actual="+reverse);}
  private static List<String> allBinaryStringsUpToFive(){List<String> out=new ArrayList<>(); out.add(""); for(int len=1;len<=5;len++){int count=1<<len; for(int mask=0;mask<count;mask++){StringBuilder sb=new StringBuilder(len); for(int i=0;i<len;i++) sb.append(((mask>>i)&1)==0?'a':'b'); out.add(sb.toString());}} return out;}
  private static String randomString(int maxLen){int len=RNG.nextInt(maxLen+1); StringBuilder sb=new StringBuilder(len); for(int i=0;i<len;i++) sb.append(ALPHABET[RNG.nextInt(ALPHABET.length)]); return sb.toString();}
  public static void main(String[] args){
    check("","",0,"both-empty"); check("abc","",0,"one-empty"); check("abcde","ace",3,"classic"); check("abc","abc",3,"identical"); check("abc","def",0,"disjoint"); check("abc","bac",2,"cross-order"); check("aaaa","aa",2,"repeated"); check("XMJYAUZ","MZJAWXU",4,"nontrivial");
    boolean left=false,right=false; try{LongestCommonSubsequence.lcsLength(null,"x");}catch(IllegalArgumentException expected){left=true;} try{LongestCommonSubsequence.lcsLength("x",null);}catch(IllegalArgumentException expected){right=true;} if(!left||!right) throw new AssertionError("null contract must throw on either input");
    List<String> exhaustive=allBinaryStringsUpToFive(); int pairCount=0; for(String a:exhaustive) for(String b:exhaustive){int expected=bruteOracle(a,b); check(a,b,expected,"exhaustive-"+pairCount); pairCount++;} if(pairCount!=3969) throw new AssertionError("unexpected exhaustive pair count="+pairCount);
    for(int i=0;i<12000;i++){String a=randomString(10),b=randomString(10); check(a,b,bruteOracle(a,b),"random-"+i);} System.out.println("PASS reviewer fixed=8 exhaustive_binary_pairs=3969 random=12000 oracle=bruteforce-subsequence null=throws symmetry=preserved");
  }
}
