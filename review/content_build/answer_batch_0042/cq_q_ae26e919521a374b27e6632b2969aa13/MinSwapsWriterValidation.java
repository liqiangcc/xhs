import java.util.*;

public final class MinSwapsWriterValidation {
    static int constructive(String s) {
        char[] a=s.toCharArray(), target=s.toCharArray();
        Arrays.sort(target);
        int swaps=0;
        for(int i=0;i<a.length;i++) {
            if(a[i]==target[i]) continue;
            int j=i+1;
            while(j<a.length && a[j]!=target[i]) j++;
            if(j==a.length) throw new AssertionError("target char missing");
            char t=a[i]; a[i]=a[j]; a[j]=t; swaps++;
        }
        if(!Arrays.equals(a,target)) throw new AssertionError("not sorted");
        return swaps;
    }
    static void permute(char[] a, int i, List<String> out) {
        if(i==a.length){out.add(new String(a));return;}
        for(int j=i;j<a.length;j++){
            char t=a[i]; a[i]=a[j]; a[j]=t;
            permute(a,i+1,out);
            t=a[i]; a[i]=a[j]; a[j]=t;
        }
    }
    static void check(String s) {
        int got=Solution.minSwapsToSort(s), want=constructive(s);
        if(got!=want) throw new AssertionError(s+" got="+got+" want="+want);
    }
    public static void main(String[] args) {
        check(""); check("a"); check("abc"); check("bac"); check("dcab"); check("fedcba");
        if(Solution.minSwapsToSort("dcab")!=3) throw new AssertionError("dcab expected 3");
        if(Solution.minSwapsToSort("fedcba")!=3) throw new AssertionError("reverse 6 expected 3");
        try { Solution.minSwapsToSort("aab"); throw new AssertionError("duplicates accepted"); } catch(IllegalArgumentException expected) {}
        try { Solution.minSwapsToSort(null); throw new AssertionError("null accepted"); } catch(NullPointerException expected) {}
        int checked=0;
        for(int n=1;n<=7;n++) {
            char[] base=new char[n]; for(int i=0;i<n;i++) base[i]=(char)('a'+i);
            List<String> ps=new ArrayList<>(); permute(base,0,ps);
            for(String s:ps){check(s);checked++;}
        }
        System.out.println("PASS fixed=8 exhaustive-distinct-permutations="+checked+" duplicates=rejected null=rejected constructive-oracle=match corrected-dcab=3");
    }
}
