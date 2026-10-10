package com.dsh.phone;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Pure parsing rules for the relay's pairing links and for the pairing cookie.
 *
 * <p>Two reasons this lives outside {@code MainActivity}:
 * <ul>
 *   <li>the relay hands out a pairing link as text (chat apps mangle it, deep links arrive as a
 *       full URL, the desktop panel can also copy just the code), so the accepted shapes have to
 *       be precise: only a {@code https://<host>/pair-accept?pair=<code>} URL is ever loaded into
 *       the WebView, and the host is remembered as the computer this phone belongs to;</li>
 *   <li>nothing here needs Android, so the rules are unit-tested on the JVM
 *       ({@code test/com/dsh/phone/PairLinksTest.java}).</li>
 * </ul>
 *
 * <p>This is the generic (pairing-mode) build: the relay host is <em>not</em> baked in, so any
 * {@code https} host is accepted as long as the path is the relay's own pairing path. The user
 * pastes the link, so showing them the host and refusing everything that is not an https pairing
 * link is the whole trust boundary.
 */
final class PairLinks {

    /** The relay mints {@code <16 hex>.dsh-market.com}, but a self-hosted relay may differ. */
    static final String RELAY_DOMAIN = ".dsh-market.com";

    /**
     * {@code https://<relay host>[:port]/pair-accept?pair=<code>} anywhere inside the pasted text.
     * The port is optional because a self-hosted relay does not have to sit on 443.
     */
    private static final Pattern PAIR_LINK = Pattern.compile(
            "https://([A-Za-z0-9.-]+(?::\\d{1,5})?)/pair-accept\\?pair=([A-Za-z0-9_-]{8,})");

    /** A bare pairing code, as copied by the panel's "copy code" action (base64url, 43 chars). */
    private static final Pattern PAIR_CODE = Pattern.compile("[A-Za-z0-9_-]{8,}");

    /**
     * Turns whatever the user pasted or tapped into the one URL that may be loaded, or {@code null}
     * when it cannot be trusted. Surrounding text is ignored and the URL is rebuilt from the matched
     * host and code.
     *
     * @param baseUrl the computer this install already belongs to, used to expand a bare pairing
     *                code; pass {@code null} when nothing is paired yet, in which case a bare code
     *                is refused (there is no way to know whose computer it belongs to).
     */
    static String normalize(String raw, String baseUrl) {
        if (raw == null) {
            return null;
        }
        String value = raw.trim();
        if (value.isEmpty()) {
            return null;
        }
        Matcher link = PAIR_LINK.matcher(value);
        if (link.find()) {
            String host = link.group(1);
            if (host == null || host.isEmpty()) {
                return null;
            }
            return "https://" + host + "/pair-accept?pair=" + link.group(2);
        }
        if (value.indexOf('/') >= 0) {
            // Link-shaped but not a pairing link (wrong scheme, wrong path).
            return null;
        }
        if (!PAIR_CODE.matcher(value).matches()) {
            return null;
        }
        if (baseUrl == null || baseUrl.isEmpty()) {
            return null;
        }
        return baseUrl + "/pair-accept?pair=" + value;
    }

    /**
     * Host of an absolute URL, or {@code null} when there is none.
     *
     * <p>Used to decide whether the WebView may follow a navigation itself. The relay answers the
     * pairing link with a 303 to {@code /pair-app?grant=...}, and Android delivers that redirect to
     * {@code shouldOverrideUrlLoading} - so before the site is remembered, the only host the app can
     * recognise is the one inside the link the user just pasted. Without this the first pairing
     * would be handed to the system browser and would look like a failure.
     */
    static String hostOf(String url) {
        if (url == null) {
            return null;
        }
        String value = url.trim();
        if (!value.startsWith("https://") && !value.startsWith("http://")) {
            return null;
        }
        Matcher link = Pattern.compile("^[a-zA-Z][a-zA-Z0-9+.-]*://([A-Za-z0-9.-]+)").matcher(value);
        if (!link.find()) {
            return null;
        }
        String host = link.group(1);
        return host.isEmpty() ? null : host;
    }

    /** {@code https://<host>} behind a normalized pairing link, or {@code null} when unparseable. */
    static String siteOf(String pairUrl) {
        if (pairUrl == null) {
            return null;
        }
        Matcher link = PAIR_LINK.matcher(pairUrl.trim());
        if (!link.find()) {
            return null;
        }
        return "https://" + link.group(1);
    }

    /** Value of {@code name} in a {@code Cookie} header, or {@code null} when it is absent/empty. */
    static String cookieValue(String header, String name) {
        if (header == null || name == null) {
            return null;
        }
        for (String part : header.split(";")) {
            String piece = part.trim();
            if (piece.startsWith(name + "=")) {
                String value = piece.substring(name.length() + 1).trim();
                return value.isEmpty() ? null : value;
            }
        }
        return null;
    }

    private PairLinks() {
    }
}
