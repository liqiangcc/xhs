import java.util.Random;

public final class KmpSearchTest {
    private static void check(String text, String pattern) {
        int actual = KmpSearch.indexOf(text, pattern);
        int expected = text.indexOf(pattern);
        if (actual != expected) throw new AssertionError("text="+text+" pattern="+pattern+" expected="+expected+" actual="+actual);
    }
    public static void main(String[] args) {
        check("", ""); check("", "a"); check("a", ""); check("aaaaa", "aaa"); check("abababca", "ababca"); check("mississippi", "issip"); check("abc", "abcd");
        Random r = new Random(20260826L);
        for (int round=0; round<5000; round++) {
            int n=r.nextInt(60), m=r.nextInt(20); StringBuilder t=new StringBuilder(), p=new StringBuilder();
            for(int i=0;i<n;i++) t.append((char)('a'+r.nextInt(4)));
            for(int i=0;i<m;i++) p.append((char)('a'+r.nextInt(4)));
            check(t.toString(),p.toString());
        }
        boolean threw=false; try { KmpSearch.indexOf(null,"a"); } catch(IllegalArgumentException e){threw=true;} if(!threw) throw new AssertionError("null text contract");
        System.out.println("PASS edges overlap fallback absent empty randomized-5000 null-contract exact-fence");
    }
}
