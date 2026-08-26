import java.math.BigInteger;

class writer_validation {
    static long modPow(long base, long exponent, long mod) {
        long result = 1 % mod;
        base = Math.floorMod(base, mod);
        while (exponent > 0) {
            if ((exponent & 1L) != 0) result = (result * base) % mod;
            base = (base * base) % mod;
            exponent >>= 1;
        }
        return result;
    }

    static boolean divisibleBy10() {
        long left = modPow(17, 400, 10);
        long right = modPow(19, 100, 10);
        return Math.floorMod(left - right, 10) == 0;
    }

    public static void main(String[] args) {
        if (modPow(17,400,10) != 1) throw new AssertionError("17^400 mod 10");
        if (modPow(19,100,10) != 1) throw new AssertionError("19^100 mod 10");
        if (!divisibleBy10()) throw new AssertionError("difference must be divisible by 10");
        BigInteger ten=BigInteger.TEN;
        BigInteger exactResidue=BigInteger.valueOf(17).pow(400).subtract(BigInteger.valueOf(19).pow(100)).mod(ten);
        if (!exactResidue.equals(BigInteger.ZERO)) throw new AssertionError("BigInteger exact residue="+exactResidue);
        long checked=0;
        for(long b=-50;b<=50;b++){
            for(long e=0;e<=200;e++){
                long got=modPow(b,e,10);
                BigInteger expected=BigInteger.valueOf(b).pow((int)e).mod(ten);
                if(got!=expected.longValue())throw new AssertionError("modPow mismatch b="+b+" e="+e+" got="+got+" expected="+expected);
                checked++;
            }
        }
        System.out.println("PASS left_mod10=1 right_mod10=1 difference_mod10=0 exact_big_integer=0 modpow_crosscheck="+checked);
    }
}
