package com.dsh.phone;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;

import java.security.SecureRandom;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/**
 * Stores the app-entry password as a PBKDF2-HMAC-SHA256 hash.
 *
 * <p>Only a random salt and the derived key are persisted; the password itself is never stored, so
 * the lock cannot be read back out of the app's private data directory. This is a local device lock
 * (it protects the app when somebody else picks up the phone) - it is deliberately independent of
 * the DSH server credential.
 */
final class LockStore {

    private static final String PREFS = "dsh_phone_lock";
    private static final String KEY_SALT = "salt";
    private static final String KEY_HASH = "hash";
    private static final String KEY_FAILS = "fails";
    private static final String KEY_UNTIL = "lockUntil";
    private static final String KEY_CRED = "credential";
    private static final String KEY_REVOKED = "credentialRevoked";
    private static final String KEY_SITE_URL = "siteUrl";
    private static final String KEY_SITE_HOST = "siteHost";

    private static final int ITERATIONS = 100_000;
    private static final int KEY_BITS = 256;
    private static final int SALT_BYTES = 16;

    /** Wrong attempts tolerated before the entry field starts cooling down. */
    private static final int FREE_ATTEMPTS = 5;
    private static final long BASE_COOLDOWN_MS = 30_000L;
    private static final long MAX_COOLDOWN_MS = 600_000L;

    private final SharedPreferences prefs;

    LockStore(Context context) {
        prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    boolean hasPassword() {
        return prefs.contains(KEY_SALT) && prefs.contains(KEY_HASH);
    }

    void setPassword(String password) {
        byte[] salt = new byte[SALT_BYTES];
        new SecureRandom().nextBytes(salt);
        byte[] hash = derive(password, salt);
        prefs.edit()
                .putString(KEY_SALT, Base64.encodeToString(salt, Base64.NO_WRAP))
                .putString(KEY_HASH, Base64.encodeToString(hash, Base64.NO_WRAP))
                .putInt(KEY_FAILS, 0)
                .putLong(KEY_UNTIL, 0L)
                .apply();
    }

    boolean verify(String password) {
        if (!hasPassword()) {
            return false;
        }
        byte[] salt = Base64.decode(prefs.getString(KEY_SALT, ""), Base64.NO_WRAP);
        byte[] expected = Base64.decode(prefs.getString(KEY_HASH, ""), Base64.NO_WRAP);
        return constantTimeEquals(expected, derive(password, salt));
    }

    void clear() {
        prefs.edit().clear().apply();
    }

    long coolDownRemainingMs() {
        long until = prefs.getLong(KEY_UNTIL, 0L);
        long now = System.currentTimeMillis();
        return until > now ? until - now : 0L;
    }

    void recordFailure() {
        int fails = prefs.getInt(KEY_FAILS, 0) + 1;
        long until = 0L;
        if (fails >= FREE_ATTEMPTS) {
            int step = Math.min(fails - FREE_ATTEMPTS, 6);
            long delay = Math.min(BASE_COOLDOWN_MS << step, MAX_COOLDOWN_MS);
            until = System.currentTimeMillis() + delay;
        }
        prefs.edit().putInt(KEY_FAILS, fails).putLong(KEY_UNTIL, until).apply();
    }

    void recordSuccess() {
        prefs.edit().putInt(KEY_FAILS, 0).putLong(KEY_UNTIL, 0L).apply();
    }

    /**
     * The pairing credential this install currently trusts. Nothing is baked into the APK in this
     * build: the credential only exists after the user paired this phone with their own computer.
     */
    String credential() {
        String stored = prefs.getString(KEY_CRED, null);
        return stored == null || stored.isEmpty() ? null : stored;
    }

    void setCredential(String deviceId) {
        prefs.edit().putString(KEY_CRED, deviceId == null ? "" : deviceId).apply();
    }

    /**
     * Base URL of the relay this install belongs to ({@code https://<id>.dsh-market.com}), learned
     * from the pairing link the user pasted. Null until the first successful pairing - the whole
     * point of this build is that the computer is chosen on the phone, not at build time.
     */
    String siteUrl() {
        String stored = prefs.getString(KEY_SITE_URL, null);
        return stored == null || stored.isEmpty() ? null : stored;
    }

    /** Host part of {@link #siteUrl()}, or null when this install is not paired yet. */
    String siteHost() {
        String stored = prefs.getString(KEY_SITE_HOST, null);
        return stored == null || stored.isEmpty() ? null : stored;
    }

    /** Remembers which computer this phone belongs to. {@code baseUrl} carries {@code https://}. */
    void setSite(String baseUrl) {
        String host = null;
        if (baseUrl != null) {
            try {
                host = java.net.URI.create(baseUrl).getHost();
            } catch (RuntimeException ignored) {
                host = null;
            }
        }
        prefs.edit()
                .putString(KEY_SITE_URL, baseUrl == null ? "" : baseUrl)
                .putString(KEY_SITE_HOST, host == null ? "" : host)
                .apply();
    }

    /**
     * True after the user wiped the local data: the baked credential must not be injected any more,
     * otherwise "forgot password" would be a way around the lock instead of a full reset.
     */
    boolean credentialRevoked() {
        return prefs.getBoolean(KEY_REVOKED, false);
    }

    void setCredentialRevoked(boolean revoked) {
        prefs.edit().putBoolean(KEY_REVOKED, revoked).apply();
    }

    private static byte[] derive(String password, byte[] salt) {
        PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, ITERATIONS, KEY_BITS);
        try {
            return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
                    .generateSecret(spec)
                    .getEncoded();
        } catch (Exception e) {
            throw new IllegalStateException("PBKDF2 unavailable", e);
        } finally {
            spec.clearPassword();
        }
    }

    private static boolean constantTimeEquals(byte[] a, byte[] b) {
        if (a == null || b == null || a.length != b.length) {
            return false;
        }
        int diff = 0;
        for (int i = 0; i < a.length; i++) {
            diff |= a[i] ^ b[i];
        }
        return diff == 0;
    }
}
