package com.dsh.phone;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Development-only check that the URLs a live /pair-app shell references actually match the
 * assets bundled into the APK. A miss means the WebView would fall back to the network for that
 * URL, which silently defeats the whole point of shipping the client inside the APK.
 *
 * <p>This exists because v1.4 first shipped a silent failure: {@code index.txt} stored absolute
 * URLs while the shell asked for relative ones (plus {@code &amp;} entities and {@code ./}
 * segments), so 88 of 89 lookups missed and every bundled asset was quietly fetched from the
 * network instead.
 *
 * <pre>
 *   # index.txt out of the APK, urls.txt from tools/shell_urls.py
 *   javac -encoding UTF-8 -d &lt;tmp&gt; java\com\dsh\phone\AssetIndex.java tools\IndexMatchCheck.java
 *   java -cp &lt;tmp&gt; com.dsh.phone.IndexMatchCheck &lt;index.txt&gt; &lt;urls.txt&gt;
 * </pre>
 */
public final class IndexMatchCheck {

    public static void main(String[] args) throws Exception {
        Reader index = new InputStreamReader(new FileInputStream(args[0]), StandardCharsets.UTF_8);
        AssetIndex table = AssetIndex.load(index);
        List<String> urls = new ArrayList<String>();
        BufferedReader in = new BufferedReader(new InputStreamReader(
                new FileInputStream(args[1]), StandardCharsets.UTF_8));
        try {
            String line;
            while ((line = in.readLine()) != null) {
                if (!line.trim().isEmpty()) {
                    urls.add(line.trim());
                }
            }
        } finally {
            in.close();
        }

        int hit = 0;
        List<String> miss = new ArrayList<String>();
        for (String url : urls) {
            AssetIndex.Entry e = table.lookup(url);
            if (e == null) {
                miss.add(url);
            } else {
                hit++;
                if (e.file().isEmpty() || e.mime().isEmpty()) {
                    System.out.println("BROKEN ENTRY for " + url);
                }
            }
        }
        System.out.println("index entries: " + table.size());
        System.out.println("shell urls: " + urls.size() + " ; hits: " + hit + " ; misses: " + miss.size());
        for (String m : miss) {
            System.out.println("   MISS " + (m.length() > 110 ? m.substring(0, 110) + "..." : m));
        }
        boolean bridge = false;
        for (String url : urls) {
            if (url.contains("/.webmcp/bridge.js")) {
                bridge = table.lookup(url) != null;
            }
        }
        System.out.println("bridge.js served from bundle: " + bridge);
    }

    private IndexMatchCheck() {
    }
}
