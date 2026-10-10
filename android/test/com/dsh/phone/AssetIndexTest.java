package com.dsh.phone;

import java.io.StringReader;

/**
 * JVM unit tests for {@link AssetIndex} - no Android, no JUnit, no network.
 *
 * <pre>
 *   javac -encoding UTF-8 -d &lt;tmp&gt; java\com\dsh\phone\AssetIndex.java test\com\dsh\phone\AssetIndexTest.java
 *   java -cp &lt;tmp&gt; com.dsh.phone.AssetIndexTest
 * </pre>
 */
public final class AssetIndexTest {

    private static final String COMBO = "plugins/??@a/client.js,@b/client.js&rev=e51b473caecb";

    private static int failed;
    private static int passed;

    public static void main(String[] args) throws Exception {
        // ---- canonicalisation ----------------------------------------------------------
        eq("bare path", "/plugins/x.js", AssetIndex.canonical("https://host/plugins/x.js"));
        eq("keeps query", "/plugins/??a,b&rev=1",
                AssetIndex.canonical("https://2df44bbae47b1cfa.dsh-market.com/plugins/??a,b&rev=1"));
        eq("keeps bare ?", "/plugins/??a,b&rev=1", AssetIndex.canonical("/plugins/??a,b&rev=1"));
        eq("drops fragment", "/assets/i.js", AssetIndex.canonical("https://host/assets/i.js#x"));
        eq("decodes percent", "/plugins/??a,b&rev=1", AssetIndex.canonical("https://host/plugins/%3F%3Fa,b&rev=1"));
        eq("decodes comma and at", "/plugins/??a@b,cd&rev=1",
                AssetIndex.canonical("https://host/plugins/%3F%3Fa%40b%2Ccd&rev=1"));
        eq("keeps plus", "/a+b", AssetIndex.canonical("https://host/a+b"));
        eq("null", null, AssetIndex.canonical(null));
        eq("trims", "/a.js", AssetIndex.canonical("  https://host/a.js  "));
        eq("port kept out", "/a.js", AssetIndex.canonical("https://host:8443/a.js"));
        eq("broken percent left alone", "/a%zz", AssetIndex.canonical("https://host/a%zz"));
        // Regression: the shell writes relative URLs (and `&amp;` entities) while index.txt is
        // absolute, so the two spellings must collapse to the same key or nothing is ever served.
        eq("roots a relative url", "/assets/index-5SrrfWpU.js",
                AssetIndex.canonical("./assets/index-5SrrfWpU.js"));
        eq("roots a bare plugin combo", "/plugins/??a,b&rev=1",
                AssetIndex.canonical("plugins/??a,b&rev=1"));
        eq("resolves single dot segment", "/assets/index-5SrrfWpU.js",
                AssetIndex.canonical("https://host/./assets/index-5SrrfWpU.js"));
        eq("decodes html entity", "/plugins/??a,b&rev=1",
                AssetIndex.canonical("plugins/??a,b&amp;rev=1"));
        eq("resolves parent segment", "/b.js", AssetIndex.canonical("https://host/a/../b.js"));
        eq("collapses duplicate slashes", "/a/b.js", AssetIndex.canonical("https://host//a//b.js"));
        eq("keeps trailing slash", "/a/", AssetIndex.canonical("https://host/a/"));

        // ---- loading and lookup --------------------------------------------------------
        String index = "# comment\n"
                + "\n"
                + "https://host/" + COMBO + "\tcombo.js\tapplication/javascript\teager\n"
                + "https://host/plugins/??@a/client.js&rev=1\tsingle.js\tapplication/javascript\tlazy\n"
                + "https://host/assets/index-5SrrfWpU.js\tidx.js\tapplication/javascript\tlazy\n"
                + "https://host/./assets/vendor-CCJJTK99.js\tvendor.js\tapplication/javascript\teager\n"
                + "short line ignored\n";
        AssetIndex loaded = AssetIndex.load(new StringReader(index));
        eq("size", "4", String.valueOf(loaded.size()));

        AssetIndex.Entry hit = loaded.lookup("https://host/" + COMBO);
        eq("combo file", "combo.js", hit.file());
        eq("combo mime", "application/javascript", hit.mime());
        eq("combo eager", "true", String.valueOf(hit.eager()));

        eq("single file", "single.js",
                loaded.lookup("https://2df44bbae47b1cfa.dsh-market.com/plugins/??@a/client.js&rev=1").file());
        eq("escaped lookup still hits", "combo.js",
                loaded.lookup("https://host/plugins/%3F%3F@a/client.js,@b/client.js&rev=e51b473caecb").file());
        eq("asset file", "idx.js", loaded.lookup("/assets/index-5SrrfWpU.js").file());
        eq("relative shell url hits absolute entry", "idx.js",
                loaded.lookup("./assets/index-5SrrfWpU.js").file());
        eq("dot-segment entry hits rooted request", "vendor.js",
                loaded.lookup("https://2df44bbae47b1cfa.dsh-market.com/assets/vendor-CCJJTK99.js").file());
        eq("entity-escaped request hits", "combo.js",
                loaded.lookup("plugins/??@a/client.js,@b/client.js&amp;rev=e51b473caecb").file());
        eq("lazy flag", "false",
                String.valueOf(loaded.lookup("https://host/assets/index-5SrrfWpU.js").eager()));
        nil("unknown url", loaded.lookup("https://host/plugins/??gone/client.js&rev=2"));
        nil("null url", loaded.lookup(null));
        eq("empty index size", "0", String.valueOf(AssetIndex.empty().size()));
        nil("empty index lookup", AssetIndex.empty().lookup("https://host/a.js"));

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

    private static void nil(String name, Object actual) {
        if (actual == null) {
            passed++;
        } else {
            failed++;
            System.out.println("FAIL " + name + "\n  expected: null\n  actual:   " + actual);
        }
    }

    private AssetIndexTest() {
    }
}
