package com.dsh.phone;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.Reader;
import java.util.ArrayDeque;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;

/**
 * Lookup table for the web assets shipped inside the APK ({@code assets/web/index.txt}).
 *
 * <p>A cold WebView load of the remote GUI pulls roughly 30 MB of content-hashed bundles
 * (two eager {@code plugins/??<modules>&rev=<hash>} combos, the module URLs listed in
 * {@code __DSH_BOOT__}, {@code assets/index-*.js|css}, {@code .webmcp/bridge.js}). Those URLs are
 * immutable, so {@code build.ps1} downloads them once and {@code MainActivity} serves them from the
 * APK instead of the phone's link. URLs the bundle does not know (e.g. after a DSH/plugin update
 * changed a {@code rev}) simply fall through to the network.
 *
 * <p>Keys are compared in a canonical form (path + query, percent-decoded) because the WebView may
 * re-encode characters that the shell wrote literally, and a miss here only costs bandwidth.
 */
final class AssetIndex {

    /** One bundled asset: the file under {@code assets/web/} and the type to serve it as. */
    static final class Entry {
        private final String file;
        private final String mime;
        private final boolean eager;

        Entry(String file, String mime, boolean eager) {
            this.file = file;
            this.mime = mime;
            this.eager = eager;
        }

        String file() {
            return file;
        }

        String mime() {
            return mime;
        }

        /** True when the shell itself references this asset in a tag, i.e. it is needed to boot. */
        boolean eager() {
            return eager;
        }
    }

    private final Map<String, Entry> byPath;
    private AssetIndex(Map<String, Entry> byPath) {
        this.byPath = byPath;
    }

    static AssetIndex empty() {
        return new AssetIndex(Collections.<String, Entry>emptyMap());
    }

    /** Reads {@code index.txt} lines of {@code <url>\t<file>\t<mime>\t<eager|lazy>}. */
    static AssetIndex load(Reader source) throws IOException {
        Map<String, Entry> entries = new HashMap<String, Entry>();
        BufferedReader reader = new BufferedReader(source);
        try {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.isEmpty() || line.charAt(0) == '#') {
                    continue;
                }
                String[] parts = line.split("\t");
                if (parts.length < 3) {
                    continue;
                }
                String key = canonical(parts[0]);
                if (key == null || key.isEmpty()) {
                    continue;
                }
                entries.put(key, new Entry(parts[1], parts[2],
                        parts.length > 3 && "eager".equals(parts[3])));
            }
        } finally {
            reader.close();
        }
        return new AssetIndex(entries);
    }

    int size() {
        return byPath.size();
    }

    Entry lookup(String url) {
        String key = canonical(url);
        return key == null ? null : byPath.get(key);
    }

    /**
     * Path + query, percent-decoded, dot-segments resolved and always rooted, so that
     * {@code plugins/??a,b&amp;rev=1}, {@code /plugins/??a%2Cb&rev=1} and
     * {@code https://host/./plugins/??a,b&amp;rev=1} all hit the same entry. The shell writes its
     * URLs relatively ({@code ./assets/x.js}) while {@code index.txt} stores them absolute, and the
     * WebView re-encodes what it likes - the lookup must not care.
     */
    static String canonical(String url) {
        if (url == null) {
            return null;
        }
        String value = url.trim();
        int fragment = value.indexOf('#');
        if (fragment >= 0) {
            value = value.substring(0, fragment);
        }
        int scheme = value.indexOf("://");
        if (scheme >= 0) {
            int slash = value.indexOf('/', scheme + 3);
            value = slash < 0 ? "/" : value.substring(slash);
        }
        value = value.replace("&amp;", "&");
        value = decode(value);
        if (!value.startsWith("/")) {
            value = "/" + value;
        }
        return normalize(value);
    }

    /** Removes {@code .} and {@code ..} segments (and duplicate slashes) from a rooted path. */
    static String normalize(String path) {
        Deque<String> segments = new ArrayDeque<String>();
        for (String segment : path.split("/", -1)) {
            if (segment.isEmpty() || ".".equals(segment)) {
                continue;
            }
            if ("..".equals(segment)) {
                if (!segments.isEmpty()) {
                    segments.removeLast();
                }
                continue;
            }
            segments.addLast(segment);
        }
        StringBuilder out = new StringBuilder();
        for (String segment : segments) {
            out.append('/').append(segment);
        }
        if (path.endsWith("/") && out.length() > 0) {
            out.append('/');
        }
        return out.length() == 0 ? "/" : out.toString();
    }

    /** {@code %XX} -> byte, without the {@code %20 = +} rule of form decoding. */
    static String decode(String value) {
        if (value.indexOf('%') < 0) {
            return value;
        }
        StringBuilder out = new StringBuilder(value.length());
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c == '%' && i + 2 < value.length()) {
                int high = Character.digit(value.charAt(i + 1), 16);
                int low = Character.digit(value.charAt(i + 2), 16);
                if (high >= 0 && low >= 0) {
                    out.append((char) ((high << 4) + low));
                    i += 2;
                    continue;
                }
            }
            out.append(c);
        }
        return out.toString();
    }
}
