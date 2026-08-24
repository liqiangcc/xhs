public final class Ipv4ToInt {
    public static int parse(String ip) {
        if (ip == null || ip.isEmpty()) throw new IllegalArgumentException("IPv4 text is required");
        int result = 0, octets = 0, value = 0, digits = 0;
        for (int i = 0; i <= ip.length(); i++) {
            char ch = i == ip.length() ? '.' : ip.charAt(i);
            if (ch == '.') {
                if (digits == 0 || octets >= 4) throw new IllegalArgumentException("IPv4 must contain exactly four non-empty octets");
                result = (result << 8) | value;
                octets++;
                value = 0;
                digits = 0;
                continue;
            }
            if (ch < '0' || ch > '9' || digits == 3) throw new IllegalArgumentException("octet must contain one to three decimal digits");
            value = value * 10 + (ch - '0');
            digits++;
            if (value > 255) throw new IllegalArgumentException("IPv4 octet out of range: " + value);
        }
        if (octets != 4) throw new IllegalArgumentException("IPv4 must contain exactly four octets");
        return result;
    }
    public static long asUnsignedLong(int bits) { return Integer.toUnsignedLong(bits); }
    private Ipv4ToInt() {}
}
