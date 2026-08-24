public final class Ipv4ToIntTest {
    public static void main(String[] args) {
        expect("0.0.0.0", 0, 0L);
        expect("1.2.3.4", 0x01020304, 16909060L);
        expect("127.0.0.1", 0x7f000001, 2130706433L);
        expect("128.0.0.0", 0x80000000, 2147483648L);
        expect("255.255.255.255", 0xffffffff, 4294967295L);
        expect("001.002.003.004", 0x01020304, 16909060L);
        reject(null); reject(""); reject("1.2.3"); reject("1.2.3.4.5"); reject("1..3.4"); reject(".1.2.3"); reject("1.2.3."); reject("256.1.1.1"); reject("0000.1.1.1"); reject("1.2.a.4"); reject("1.2.-1.4"); reject("1.2. 3.4");
        System.out.println("PASS valid=6 invalid=12 unsigned-boundaries=2 leading-zero-contract=decimal");
    }
    private static void expect(String ip, int expectedBits, long expectedUnsigned) {
        int actual = Ipv4ToInt.parse(ip);
        if (actual != expectedBits) throw new AssertionError(ip + " bits");
        if (Ipv4ToInt.asUnsignedLong(actual) != expectedUnsigned) throw new AssertionError(ip + " unsigned");
    }
    private static void reject(String ip) {
        try { Ipv4ToInt.parse(ip); throw new AssertionError("expected rejection: " + ip); }
        catch (IllegalArgumentException expected) { }
    }
    private Ipv4ToIntTest() {}
}
