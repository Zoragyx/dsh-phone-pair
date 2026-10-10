/**
 * Throw a real pairing link at {@link PairLinks} and print what the app would do with it.
 *
 * Used by tools/pair_e2e.ps1 so the parser is checked against a link the DSH instance actually
 * issued - not against a hand-written sample.
 */

package com.dsh.phone;

public final class PairLinkCheck {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("usage: PairLinkCheck <pair-link> [expected-host]");
            System.exit(2);
        }
        String raw = args[0];
        String expectedHost = args.length > 1 ? args[1] : null;

        String site = PairLinks.siteOf(raw);
        String normalized = PairLinks.normalize(raw, null);
        System.out.println("raw        : " + raw);
        System.out.println("siteOf     : " + site);
        System.out.println("normalize  : " + normalized + "  (no base yet - first run)");

        boolean ok = true;
        if (site == null) {
            System.out.println("FAIL: siteOf returned null - the app could not learn its computer");
            ok = false;
        } else if (expectedHost != null && !site.equals("https://" + expectedHost)) {
            System.out.println("FAIL: siteOf gave " + site + ", expected host " + expectedHost);
            ok = false;
        }
        if (!raw.equals(normalized)) {
            System.out.println("FAIL: normalize changed the link to " + normalized);
            ok = false;
        }
        // Once the phone knows its site, the same link must still parse - and the bare code too.
        if (site != null) {
            String again = PairLinks.normalize(raw, site);
            String code = codeOf(raw);
            String bare = PairLinks.normalize(code, site);
            if (!raw.equals(again)) {
                System.out.println("FAIL: normalize with a base gave " + again);
                ok = false;
            }
            if (!raw.equals(bare)) {
                System.out.println("FAIL: bare code with a base gave " + bare);
                ok = false;
            }
            System.out.println("bare code  : " + bare);
        }
        System.out.println(ok ? "pair-link check: OK" : "pair-link check: FAILED");
        if (!ok) {
            System.exit(1);
        }
    }

    private static String codeOf(String url) {
        int at = url.indexOf("pair=");
        return at < 0 ? "" : url.substring(at + 5);
    }

    private PairLinkCheck() {
    }
}
