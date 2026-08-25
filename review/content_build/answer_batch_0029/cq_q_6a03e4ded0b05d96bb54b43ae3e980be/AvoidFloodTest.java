import java.util.HashSet;
import java.util.Set;

final class AvoidFloodTest {
    private static void expectPossible(int[] rains) {
        int[] ans = AvoidFlood.avoidFlood(rains);
        if (ans.length != rains.length) throw new AssertionError("expected possible schedule");
        assertValid(rains, ans);
    }

    private static void expectImpossible(int[] rains) {
        int[] ans = AvoidFlood.avoidFlood(rains);
        if (ans.length != 0) throw new AssertionError("expected impossible schedule");
    }

    private static void assertValid(int[] rains, int[] ans) {
        Set<Integer> full = new HashSet<>();
        for (int i = 0; i < rains.length; i++) {
            if (rains[i] > 0) {
                if (ans[i] != -1) throw new AssertionError("rainy day must be -1 at " + i);
                if (!full.add(rains[i])) throw new AssertionError("flood at day " + i + " lake " + rains[i]);
            } else {
                if (ans[i] <= 0) throw new AssertionError("dry day must name positive lake");
                full.remove(ans[i]);
            }
        }
    }

    public static void main(String[] args) {
        expectPossible(new int[]{1,2,3,4});
        expectPossible(new int[]{1,2,0,0,2,1});
        expectImpossible(new int[]{1,2,0,1,2});
        expectPossible(new int[]{69,0,0,0,69});
        expectPossible(new int[]{1,0,1});
        expectImpossible(new int[]{1,1});
        expectPossible(new int[]{});
        boolean nullRejected=false;
        try { AvoidFlood.avoidFlood(null); } catch (IllegalArgumentException expected) { nullRejected=true; }
        if (!nullRejected) throw new AssertionError("null must be rejected");
        boolean negativeRejected=false;
        try { AvoidFlood.avoidFlood(new int[]{1,-1,0}); } catch (IllegalArgumentException expected) { negativeRejected=true; }
        if (!negativeRejected) throw new AssertionError("negative rain id must be rejected");
        System.out.println("PASS official-shapes=3 sparse-dry=yes exact-window=yes immediate-repeat=impossible empty=yes null=rejected negative=rejected");
    }
}
