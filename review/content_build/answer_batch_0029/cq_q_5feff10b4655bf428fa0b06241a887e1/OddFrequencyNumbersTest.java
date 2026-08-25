import java.util.Arrays;

final class OddFrequencyNumbersTest {
    private static void expectOne(int expected, int[] nums) {
        int actual = OddFrequencyNumbers.findOneOdd(nums);
        if (actual != expected) throw new AssertionError("expected=" + expected + " actual=" + actual);
    }

    private static void expectTwo(int x, int y, int[] nums) {
        int[] actual = OddFrequencyNumbers.findTwoOdd(nums);
        Arrays.sort(actual);
        int[] expected = new int[]{x, y};
        Arrays.sort(expected);
        if (!Arrays.equals(actual, expected)) throw new AssertionError("expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
    }

    public static void main(String[] args) {
        expectOne(7, new int[]{2, 2, 7, 3, 3});
        expectOne(-5, new int[]{-5, 4, 4, 9, 9, -8, -8});
        expectOne(Integer.MIN_VALUE, new int[]{1, 1, Integer.MIN_VALUE});
        expectTwo(5, 9, new int[]{1, 1, 2, 2, 5, 7, 7, 9});
        expectTwo(-7, 12, new int[]{-7, 3, 3, 12, 8, 8});
        expectTwo(Integer.MIN_VALUE, 0, new int[]{Integer.MIN_VALUE, 4, 4, 0, 6, 6});
        boolean nullRejected=false;
        try { OddFrequencyNumbers.findOneOdd(null); } catch (IllegalArgumentException expected) { nullRejected=true; }
        if (!nullRejected) throw new AssertionError("null must be rejected explicitly");
        boolean badTwoRejected=false;
        try { OddFrequencyNumbers.findTwoOdd(new int[]{1,1,2,2}); } catch (IllegalArgumentException expected) { badTwoRejected=true; }
        if (!badTwoRejected) throw new AssertionError("two-odd contract violation must be rejected");
        System.out.println("PASS one-odd=3 two-odd=3 negatives=supported min-value=supported null=rejected bad-two=rejected");
    }
}
