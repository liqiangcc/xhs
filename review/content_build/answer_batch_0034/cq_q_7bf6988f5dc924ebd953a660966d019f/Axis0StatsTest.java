import java.util.Arrays;

public final class Axis0StatsTest {
    private static void close(double actual, double expected, double eps, String name) {
        if (Math.abs(actual-expected) > eps) throw new AssertionError(name+" expected="+expected+" actual="+actual);
    }
    private static void throwsIAE(Runnable r, String name) {
        try { r.run(); throw new AssertionError(name+" expected IllegalArgumentException"); }
        catch (IllegalArgumentException expected) { }
    }
    public static void main(String[] args) {
        double[][] a={{1,2},{3,4},{5,6}};
        var s=Axis0Stats.population(a);
        close(s.mean()[0],3,1e-12,"mean0"); close(s.mean()[1],4,1e-12,"mean1");
        close(s.variance()[0],8.0/3.0,1e-12,"var0"); close(s.variance()[1],8.0/3.0,1e-12,"var1");
        var single=Axis0Stats.population(new double[][]{{7,9}});
        close(single.mean()[0],7,0,"single mean"); close(single.variance()[0],0,0,"single variance");
        var large=Axis0Stats.population(new double[][]{{1_000_000_000_001d},{1_000_000_000_002d},{1_000_000_000_003d}});
        close(large.mean()[0],1_000_000_000_002d,1e-9,"large mean"); close(large.variance()[0],2.0/3.0,1e-12,"large variance");
        if(!Arrays.deepEquals(a,new double[][]{{1,2},{3,4},{5,6}})) throw new AssertionError("input mutated");
        throwsIAE(() -> Axis0Stats.population(null),"null");
        throwsIAE(() -> Axis0Stats.population(new double[][]{}),"empty rows");
        throwsIAE(() -> Axis0Stats.population(new double[][]{{}}),"empty cols");
        throwsIAE(() -> Axis0Stats.population(new double[][]{{1,2},{3}}),"ragged");
        throwsIAE(() -> Axis0Stats.population(new double[][]{{Double.NaN}}),"nan");
        System.out.println("PASS axis0 mean population-variance welford single-row large-offset shape finite immutable-input");
    }
}
