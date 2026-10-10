package com.dsh.phone;

/**
 * JVM unit tests for {@link PairLinks} - no Android, no JUnit, no network.
 *
 * <pre>
 *   javac -encoding UTF-8 -d &lt;tmp&gt; java\com\dsh\phone\PairLinks.java test\com\dsh\phone\PairLinksTest.java
 *   java -cp &lt;tmp&gt; com.dsh.phone.PairLinksTest
 * </pre>
 */
public final class PairLinksTest {

    private static final String BASE = "https://2df44bbae47b1cfa.dsh-market.com";
    private static final String CODE = "5404800873d65c8554f96a35826a2d86";
    private static int failed;
    private static int passed;

    public static void main(String[] args) {
        // ---- full links ---------------------------------------------------------------
        eq("plain link", BASE + "/pair-accept?pair=" + CODE,
                PairLinks.normalize(BASE + "/pair-accept?pair=" + CODE, BASE));
        eq("surrounded by chat text",
                BASE + "/pair-accept?pair=" + CODE,
                PairLinks.normalize("打开这个链接 " + BASE + "/pair-accept?pair=" + CODE + " 完成配对", BASE));
        eq("link with whitespace around it",
                BASE + "/pair-accept?pair=" + CODE,
                PairLinks.normalize("  \t" + BASE + "/pair-accept?pair=" + CODE + "\n", BASE));
        eq("43 char code with url-safe alphabet", BASE + "/pair-accept?pair=" + CODE, PairLinks
                .normalize(BASE + "/pair-accept?pair=" + CODE, BASE));
        eq("wrapped in a redirector", BASE + "/pair-accept?pair=" + CODE,
                PairLinks.normalize("https://t.co/x?u=https://2df44bbae47b1cfa.dsh-market.com"
                        + "/pair-accept?pair=" + CODE, BASE));

        // ---- refused links ------------------------------------------------------------
        nil("http link", PairLinks.normalize("http://2df44bbae47b1cfa.dsh-market.com/pair-accept?pair=" + CODE, BASE));
        nil("wrong path", PairLinks.normalize("https://2df44bbae47b1cfa.dsh-market.com/pair-apply?pair=" + CODE, BASE));
        nil("short code", PairLinks.normalize(BASE + "/pair-accept?pair=abc", BASE));
        nil("no code", PairLinks.normalize(BASE + "/pair-accept", BASE));
        nil("empty", PairLinks.normalize("", BASE));
        nil("only spaces", PairLinks.normalize("   ", BASE));
        nil("null", PairLinks.normalize(null, BASE));

        // ---- any https relay is accepted: this build must work with someone else's computer --
        eq("other domain is fine (generic build)", "https://evil.com/pair-accept?pair=" + CODE,
                PairLinks.normalize("https://evil.com/pair-accept?pair=" + CODE, BASE));
        eq("spoofed suffix is fine too", "https://dsh-market.com.evil.com/pair-accept?pair=" + CODE,
                PairLinks.normalize("https://dsh-market.com.evil.com/pair-accept?pair=" + CODE, BASE));
        eq("self-hosted relay", "https://dsh.example.com/pair-accept?pair=" + CODE,
                PairLinks.normalize("https://dsh.example.com/pair-accept?pair=" + CODE, BASE));
        eq("relay with a port", "https://dsh.example.com:8443/pair-accept?pair=" + CODE,
                PairLinks.normalize("https://dsh.example.com:8443/pair-accept?pair=" + CODE, BASE));
        eq("surrounding text with another host", "https://dsh.example.com/pair-accept?pair=" + CODE,
                PairLinks.normalize("配对链接：https://dsh.example.com/pair-accept?pair=" + CODE, BASE));

        // ---- the host behind a link becomes the paired computer -------------------------
        eq("site of a relay link", "https://2df44bbae47b1cfa.dsh-market.com",
                PairLinks.siteOf(BASE + "/pair-accept?pair=" + CODE));
        eq("site keeps an explicit port", "https://dsh.example.com:8443",
                PairLinks.siteOf("https://dsh.example.com:8443/pair-accept?pair=" + CODE));
        nil("site of a bare code", PairLinks.siteOf(CODE));
        nil("site of null", PairLinks.siteOf(null));
        nil("site of an http link", PairLinks.siteOf("http://evil.com/pair-accept?pair=" + CODE));

        // ---- navigating inside the app: the redirect after pairing has to stay in the WebView --
        eq("host of a pairing link", "2df44bbae47b1cfa.dsh-market.com", PairLinks.hostOf(
                BASE + "/pair-accept?pair=" + CODE));
        eq("host of the grant redirect", "2df44bbae47b1cfa.dsh-market.com",
                PairLinks.hostOf(BASE + "/pair-app?grant=abc"));
        eq("host drops the port", "dsh.example.com",
                PairLinks.hostOf("https://dsh.example.com:8443/pair-accept?pair=" + CODE));
        eq("host of the shell root", "dsh.example.com", PairLinks.hostOf("https://dsh.example.com/"));
        eq("host trims whitespace", "dsh.example.com", PairLinks.hostOf("  https://dsh.example.com/x  "));
        nil("host of a relative path", PairLinks.hostOf("/pair-app"));
        nil("host of a bare code", PairLinks.hostOf(CODE));
        nil("host of empty", PairLinks.hostOf(""));
        nil("host of null", PairLinks.hostOf(null));
        nil("host of a javascript url", PairLinks.hostOf("javascript:alert(1)"));

        // ---- bare codes ---------------------------------------------------------------
        eq("bare code", BASE + "/pair-accept?pair=" + CODE, PairLinks.normalize(CODE, BASE));
        eq("padded bare code", BASE + "/pair-accept?pair=" + CODE, PairLinks.normalize("  " + CODE + " ", BASE));
        nil("bare code without a paired computer", PairLinks.normalize(CODE, null));
        nil("bare code with empty base", PairLinks.normalize(CODE, ""));
        nil("bare code with ampersand", PairLinks.normalize("abcdefgh&x=1", BASE));
        nil("bare code with question mark", PairLinks.normalize("abcdefgh?x=1", BASE));
        nil("bare code with hash", PairLinks.normalize("abcdefgh#x", BASE));
        nil("bare code with space inside", PairLinks.normalize("abc defgh", BASE));
        nil("bare code too short", PairLinks.normalize("abcdefg", BASE));
        nil("chinese text", PairLinks.normalize("配对码", BASE));

        // ---- cookie header ------------------------------------------------------------
        eq("cookie found", "deadbeef",
                PairLinks.cookieValue("other=1; dsh_pair=deadbeef; tail=2", "dsh_pair"));
        eq("cookie first", "deadbeef", PairLinks.cookieValue("dsh_pair=deadbeef", "dsh_pair"));
        nil("cookie empty", PairLinks.cookieValue("dsh_pair=", "dsh_pair"));
        nil("cookie blank", PairLinks.cookieValue("dsh_pair=  ", "dsh_pair"));
        nil("cookie absent", PairLinks.cookieValue("other=1", "dsh_pair"));
        nil("cookie prefix collision", PairLinks.cookieValue("x_dsh_pair=deadbeef", "dsh_pair"));
        nil("cookie null header", PairLinks.cookieValue(null, "dsh_pair"));
        nil("cookie null name", PairLinks.cookieValue("dsh_pair=deadbeef", null));

        System.out.println("passed=" + passed + " failed=" + failed);
        if (failed > 0) {
            System.exit(1);
        }
    }

    private static void eq(String name, String expected, String actual) {
        if (expected == null ? actual == null : expected.equals(actual)) {
            passed++;
        } else {
            failed++;
            System.out.println("FAIL " + name + "\n  expected: " + expected + "\n  actual:   " + actual);
        }
    }

    private static void nil(String name, String actual) {
        eq(name, null, actual);
    }

    private PairLinksTest() {
    }
}
