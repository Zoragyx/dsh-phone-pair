package com.dsh.phone;

// The application id of this build is com.dsh.phone.pair (so it can sit next to the pre-paired
// build), which is also where aapt2 generates the resource class.
import com.dsh.phone.pair.R;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemClock;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * DSH phone shell: a password-gated WebView that keeps the DSH web UI cached on the device.
 *
 * <p>Why a WebView and not just a browser bookmark:
 * <ul>
 *   <li>the password screen is native and instant - it never waits on the network;</li>
 *   <li>the WebView cache, DOM storage and service-worker storage live in the app's private data
 *       directory, and the ~28 MB of content-hashed client bundles ship inside the APK (see
 *       {@link AssetIndex}), so the GUI paints without waiting on the phone's slow link;</li>
 *   <li>the pairing cookie is installed into this app's own cookie jar at startup, so there is no
 *       QR scan on each install.</li>
 * </ul>
 */
public class MainActivity extends Activity {

    private static final String COOKIE_NAME = "dsh_pair";
    private static final long COOKIE_MAX_AGE_SEC = 31_536_000L;

    /** Relock after the app has been in the background for this long. 0 = every single time. */
    private static final long RELOCK_GRACE_MS = 0L;

    private static final int REQ_FILE = 4711;

    /** Contents of the APK's assets/ that back the client bundles; see AssetIndex. */
    private static final String ASSET_INDEX = "web/index.txt";
    private static final String ASSET_PREFIX = "web/";

    private static final int BG = 0xFF0B1020;
    private static final int PANEL = 0xFF161C31;
    private static final int FG = 0xFFEAF0FF;
    private static final int MUTED = 0xFF8A94B0;
    private static final int ACCENT = 0xFF4C7DFF;
    private static final int DANGER = 0xFFFF6B6B;

    private LockStore lock;
    private FrameLayout root;

    private View lockView;
    private WebView web;
    private View loadingOverlay;
    private TextView loadingLabel;
    private View errorOverlay;
    private TextView errorLabel;

    private boolean unlocked;
    private long backgroundedAt;
    private boolean suppressRelock;
    private boolean forceFreshLoad;

    private ValueCallback<Uri[]> fileCallback;
    private EditText unlockField;

    /** Bundled web bundles, loaded on first use (shouldInterceptRequest runs off the UI thread). */
    private volatile AssetIndex assetIndex;

    /** A pairing link that still has to be opened: from a tapped deep link or pasted by hand. */
    private String pendingPairUrl;
    /** Credential in use when a pairing load started, so the newly issued one can be spotted. */
    private String credentialAtPairStart;
    /** The pairing link currently being opened; its host is what tells us which computer this is. */
    private String pairingUrl;
    private boolean pairingInFlight;
    private View pairOverlay;
    private EditText pairField;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        lock = new LockStore(this);
        root = new FrameLayout(this);
        root.setBackgroundColor(BG);
        setContentView(root);
        // Read the launch intent first, so the lock screen can already say "pairing link received".
        handlePairIntent(getIntent());
        showLock();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handlePairIntent(intent);
        if (unlocked && pendingPairUrl != null && web != null) {
            hidePairOverlay();
            loadStart();
        }
    }

    // ---------------------------------------------------------------- lock screen

    private void showLock() {
        unlocked = false;
        if (lockView != null) {
            root.removeView(lockView);
        }
        boolean setup = !lock.hasPassword();

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);

        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setGravity(Gravity.CENTER_HORIZONTAL);
        col.setPadding(dp(30), dp(48), dp(30), dp(48));
        scroll.addView(col, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.mipmap.ic_launcher);
        int logoSide = dp(92);
        LinearLayout.LayoutParams logoParams = new LinearLayout.LayoutParams(logoSide, logoSide);
        logoParams.bottomMargin = dp(20);
        col.addView(logo, logoParams);

        col.addView(label("DSH 手机版", 25, FG, true), spaced(0, dp(6)));

        String hintText;
        if (pendingPairUrl != null) {
            hintText = "已收到配对链接 · 输入密码后自动完成配对";
        } else if (lock.credentialRevoked()) {
            hintText = "本机配对已清除 · 进入后请重新配对";
        } else {
            hintText = setup ? "首次使用 · 请为这台手机设置进入密码" : "输入密码后才能进入";
        }
        TextView hint = label(hintText, 14, MUTED, false);
        hint.setGravity(Gravity.CENTER);
        col.addView(hint, spaced(0, dp(4)));

        TextView note = label(
                setup
                        ? "密码只保存在本机（PBKDF2 加密），忘记后可随时重设。"
                        : "密码只保存在本机，请勿告诉他人。",
                12, MUTED, false);
        note.setGravity(Gravity.CENTER);
        col.addView(note, spaced(0, dp(22)));

        final EditText first = passwordField(setup ? "设置密码（至少 4 位）" : "密码");
        col.addView(first, fullWidth(spaced(0, dp(10))));

        final EditText second = setup ? passwordField("再输入一次") : null;
        if (second != null) {
            col.addView(second, fullWidth(spaced(0, dp(10))));
        }
        unlockField = first;

        final TextView status = label("", 13, DANGER, false);
        status.setGravity(Gravity.CENTER);
        col.addView(status, fullWidth(spaced(0, dp(6))));

        Button submit = new Button(this);
        submit.setText(setup ? "设置并进入" : "进入");
        submit.setTextSize(16);
        submit.setAllCaps(false);
        submit.setTextColor(Color.WHITE);
        submit.setBackground(rounded(ACCENT, dp(14)));
        LinearLayout.LayoutParams submitParams = fullWidth(spaced(0, dp(18)));
        submitParams.height = dp(50);
        col.addView(submit, submitParams);

        View.OnClickListener go = v -> attemptUnlock(setup, first, second, status, submit);
        submit.setOnClickListener(go);

        Button settings = new Button(this);
        settings.setText("设置 / 帮助");
        settings.setTextSize(13);
        settings.setAllCaps(false);
        settings.setTextColor(MUTED);
        settings.setBackgroundColor(Color.TRANSPARENT);
        settings.setOnClickListener(v -> openSettings());
        col.addView(settings, fullWidth(spaced(0, dp(4))));

        lockView = scroll;
        root.addView(lockView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        first.requestFocus();
    }

    private void attemptUnlock(boolean setup, EditText first, EditText second, TextView status,
                               Button submit) {
        long cool = lock.coolDownRemainingMs();
        if (cool > 0) {
            status.setText("尝试次数过多，请 " + ((cool + 999) / 1000) + " 秒后再试");
            return;
        }
        final String value = first.getText().toString();
        if (setup) {
            String again = second == null ? "" : second.getText().toString();
            if (value.length() < 4) {
                status.setText("密码至少 4 位");
                return;
            }
            if (!value.equals(again)) {
                status.setText("两次输入的密码不一致");
                return;
            }
            submit.setEnabled(false);
            status.setTextColor(MUTED);
            status.setText("正在保存…");
            new Thread(() -> {
                lock.setPassword(value);
                runOnUiThread(() -> {
                    submit.setEnabled(true);
                    status.setTextColor(DANGER);
                    status.setText("");
                    toast("密码已设置");
                    revealWeb();
                });
            }, "dsh-set-password").start();
            return;
        }

        if (value.isEmpty()) {
            status.setText("请输入密码");
            return;
        }
        submit.setEnabled(false);
        status.setTextColor(MUTED);
        status.setText("正在校验…");
        final LockStore store = lock;
        new Thread(() -> {
            final boolean ok = store.verify(value);
            runOnUiThread(() -> {
                submit.setEnabled(true);
                status.setTextColor(DANGER);
                if (ok) {
                    store.recordSuccess();
                    status.setText("");
                    first.setText("");
                    revealWeb();
                } else {
                    store.recordFailure();
                    status.setText("密码不正确");
                    long wait = store.coolDownRemainingMs();
                    if (wait > 0) {
                        status.setText("密码不正确，请 " + ((wait + 999) / 1000) + " 秒后再试");
                    }
                }
            });
        }, "dsh-verify-password").start();
    }

    // ---------------------------------------------------------------- web view

    private void revealWeb() {
        unlocked = true;
        if (web == null) {
            createWebView();
        }
        if (lockView != null) {
            root.removeView(lockView);
            lockView = null;
        }
        web.setVisibility(View.VISIBLE);
        if (needsPairing()) {
            // The credential was wiped by a reset: loading the UI would only show the plugin's
            // "pairing expired" page, so ask for a fresh pairing link instead.
            showPairOverlay();
            return;
        }
        if (web.getUrl() == null) {
            loadStart();
        }
    }

    /** True when this install has no usable pairing yet and has to pair with a computer first. */
    private boolean needsPairing() {
        return pendingPairUrl == null
                && (siteUrl() == null || activeCredential() == null || lock.credentialRevoked());
    }

    private void createWebView() {
        web = new WebView(this);
        web.setBackgroundColor(BG);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setJavaScriptCanOpenWindowsAutomatically(true);
        s.setSupportMultipleWindows(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);
        s.setGeolocationEnabled(false);
        s.setSaveFormData(false);
        // Offline-first: the shell and its content-hashed bundles are served from the app cache
        // whenever they are present, which is what makes a repeat launch instant on a slow link.
        s.setCacheMode(WebSettings.LOAD_CACHE_ELSE_NETWORK);
        String ua = s.getUserAgentString();
        s.setUserAgentString(ua + " DSH-Phone-Pair/1.0");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                // Android hands redirects to this callback too, and pairing is exactly one redirect
                // (/pair-accept -> /pair-app?grant=...). While the site is still being learned the
                // only recognisable host is the one in the link the user pasted, so that host - not
                // just an already-paired one - has to stay inside the WebView.
                String host = pairingHost();
                if (uri != null && host != null && host.equalsIgnoreCase(uri.getHost())) {
                    return false;
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                    // No browser installed - keep the navigation inside the app instead.
                    return false;
                }
                return true;
            }

            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return serveBundledAsset(request);
            }

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                // /pair-accept answers with a 303 that carries the new device cookie: adopt it the
                // moment it lands, so a slow first load cannot lose a pairing that already worked.
                if (pairingInFlight && adoptIssuedCredential()) {
                    pairingInFlight = false;
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                hideLoading();
                if (pairingInFlight) {
                    finishPairing();
                }
                if (forceFreshLoad) {
                    forceFreshLoad = false;
                    view.getSettings().setCacheMode(WebSettings.LOAD_CACHE_ELSE_NETWORK);
                }
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        WebResourceError error) {
                if (request != null && request.isForMainFrame()) {
                    showError(String.valueOf(error.getDescription()));
                }
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (fileCallback != null) {
                    fileCallback.onReceiveValue(null);
                }
                fileCallback = callback;
                suppressRelock = true;
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                try {
                    startActivityForResult(Intent.createChooser(intent, "选择文件"), REQ_FILE);
                    return true;
                } catch (Exception e) {
                    fileCallback = null;
                    suppressRelock = false;
                    return false;
                }
            }

            @Override
            public boolean onCreateWindow(WebView view, boolean isDialog, boolean isUserGesture,
                                          android.os.Message resultMsg) {
                // Keep target=_blank navigations in this WebView rather than spawning a window.
                return false;
            }
        });

        web.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> {
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
            } catch (Exception ignored) {
                toast("无法打开下载链接");
            }
        });

        applyPairingCookie();

        root.addView(web, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        buildLoadingOverlay();
        buildErrorOverlay();
    }

    /**
     * Installs the pairing credential into this app's own cookie jar. The WebView keeps it on disk,
     * so every later launch is already paired and never needs the QR code again.
     *
     * <p>The credential baked into the APK at build time is only the bootstrap: a device obtained
     * by re-pairing on the phone wins over it, and a wiped install injects nothing at all - that is
     * what stops "forgot password" from being a way around the lock.
     */
    private void applyPairingCookie() {
        CookieManager cm = CookieManager.getInstance();
        cm.setAcceptCookie(true);
        cm.setAcceptThirdPartyCookies(web, false);
        String base = siteUrl();
        String credential = activeCredential();
        if (lock.credentialRevoked() || base == null || credential == null) {
            // Unpaired (this build starts that way) or wiped: inject nothing at all.
            cm.removeAllCookies(null);
            cm.flush();
            return;
        }
        cm.setCookie(base,
                COOKIE_NAME + "=" + credential
                        + "; path=/; max-age=" + COOKIE_MAX_AGE_SEC + "; secure; httponly");
        cm.flush();
    }

    /** The device this install authenticates as; null until the user pairs with a computer. */
    private String activeCredential() {
        return lock.credential();
    }

    /** The computer this phone is paired with, or null before the first pairing. */
    private String siteUrl() {
        return lock.siteUrl();
    }

    private String siteHost() {
        return lock.siteHost();
    }

    /**
     * Host the WebView is allowed to navigate on its own: the paired computer once there is one,
     * otherwise the computer named by the link being paired right now.
     */
    private String pairingHost() {
        String paired = siteHost();
        if (paired != null) {
            return paired;
        }
        String pending = pairingUrl != null ? pairingUrl : pendingPairUrl;
        return PairLinks.hostOf(pending);
    }

    /** {@code /pair-app} on the paired computer, or null while this install is unpaired. */
    private String startUrl() {
        String base = siteUrl();
        return base == null ? null : base + "/pair-app";
    }

    /** The current value of the pairing cookie, or null when this app has none. */
    private String readPairCookie() {
        String base = siteUrl();
        if (base == null) {
            return null;
        }
        return PairLinks.cookieValue(CookieManager.getInstance().getCookie(base), COOKIE_NAME);
    }

    /** Parsed assets/web/index.txt, or an empty index when the APK has none. */
    private AssetIndex assets() {
        AssetIndex current = assetIndex;
        if (current == null) {
            synchronized (this) {
                current = assetIndex;
                if (current == null) {
                    try {
                        current = AssetIndex.load(new InputStreamReader(
                                getAssets().open(ASSET_INDEX), "UTF-8"));
                    } catch (Exception error) {
                        current = AssetIndex.empty();
                    }
                    assetIndex = current;
                }
            }
        }
        return current;
    }

    /**
     * Serves the client bundles that ship inside the APK, so a cold start does not have to pull
     * ~30 MB over the phone's link. Unknown URLs (a bundle the desktop has since re-built) return
     * null, which lets the WebView fetch them normally.
     */
    private WebResourceResponse serveBundledAsset(WebResourceRequest request) {
        if (request == null || !"GET".equals(request.getMethod())) {
            return null;
        }
        Uri url = request.getUrl();
        // AssetIndex.canonical() ignores the origin on purpose (the shell asks relatively and the
        // WebView re-encodes), so pin the lookup to the paired host: no other origin should ever be
        // handed the bundled client.
        String host = siteHost();
        if (url == null || !"https".equals(url.getScheme()) || host == null
                || !host.equalsIgnoreCase(url.getHost())) {
            return null;
        }
        AssetIndex.Entry entry = assets().lookup(String.valueOf(url));
        if (entry == null) {
            return null;
        }
        try {
            WebResourceResponse response = new WebResourceResponse(entry.mime(), null,
                    getAssets().open(ASSET_PREFIX + entry.file()));
            Map<String, String> headers = new HashMap<String, String>();
            // Content-addressed bundles: safe to pin, and it keeps the WebView cache warm too.
            headers.put("Cache-Control", "public, max-age=31536000, immutable");
            response.setResponseHeaders(headers);
            return response;
        } catch (IOException error) {
            return null;
        }
    }

    private void loadStart() {
        if (pendingPairUrl == null && startUrl() == null) {
            // Nothing is paired yet (this build ships without a baked credential): the pairing form
            // is the only useful screen.
            showPairOverlay();
            return;
        }
        web.getSettings().setCacheMode(WebSettings.LOAD_CACHE_ELSE_NETWORK);
        String target = startUrl();
        if (pendingPairUrl != null) {
            // A fresh pairing link makes the server issue a new device cookie (303 to
            // /pair-app?grant=...) which the WebView stores; finishPairing() then adopts it, and
            // the link's host becomes the computer this install belongs to.
            target = pendingPairUrl;
            pairingUrl = target;
            pendingPairUrl = null;
            credentialAtPairStart = activeCredential();
            // Measured relay behaviour: /pair-accept answers a request that already carries a valid
            // dsh_pair cookie with 303 but *no* new cookie, so a re-pair would look like a failure.
            // Dropping the cookie first forces the relay to mint a fresh device for this install.
            CookieManager cookies = CookieManager.getInstance();
            cookies.removeAllCookies(null);
            cookies.flush();
            pairingInFlight = true;
            hidePairOverlay();
            showLoading("正在完成配对…");
        } else {
            showLoading("正在加载界面…");
        }
        web.loadUrl(target);
    }

    private void finishPairing() {
        pairingInFlight = false;
        if (adoptIssuedCredential()) {
            return;
        }
        // Unchanged credential: the link was stale, already used, or the network dropped.
        // Put the previous credential back, so a bad link cannot strand a working install.
        pairingUrl = null;
        applyPairingCookie();
        toast("配对失败：配对链接可能已过期，请在电脑上重新生成");
        showPairOverlay();
    }

    /** Stores a freshly issued device cookie; true when the stored credential changed. */
    private boolean adoptIssuedCredential() {
        String issued = readPairCookie();
        if (issued != null && !issued.equals(credentialAtPairStart)) {
            credentialAtPairStart = null;
            String site = PairLinks.siteOf(pairingUrl);
            if (site != null) {
                // The link the user pasted decides which computer this phone now talks to; every
                // later request, cookie and bundled-asset lookup is scoped to it.
                lock.setSite(site);
            }
            pairingUrl = null;
            lock.setCredential(issued);
            lock.setCredentialRevoked(false);
            toast("配对成功：" + site);
            return true;
        }
        return false;
    }

    private void reloadForcing() {
        if (web == null) {
            return;
        }
        forceFreshLoad = true;
        web.clearCache(true);
        web.getSettings().setCacheMode(WebSettings.LOAD_NO_CACHE);
        showLoading("正在重新下载界面…");
        String target = startUrl();
        if (target != null) {
            web.loadUrl(target);
        }
    }

    /** Tears the WebView down completely so the next unlock rebuilds it from scratch. */
    private void destroyWeb() {
        for (View v : new View[]{web, loadingOverlay, errorOverlay, pairOverlay}) {
            if (v != null) {
                root.removeView(v);
            }
        }
        if (web != null) {
            web.destroy();
        }
        web = null;
        loadingOverlay = null;
        errorOverlay = null;
        loadingLabel = null;
        errorLabel = null;
        pairOverlay = null;
        pairField = null;
    }

    // ---------------------------------------------------------------- overlays

    private void buildLoadingOverlay() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setBackgroundColor(BG);
        ProgressBar bar = new ProgressBar(this);
        box.addView(bar, new LinearLayout.LayoutParams(dp(44), dp(44)));
        loadingLabel = label("正在加载界面…", 14, MUTED, false);
        loadingLabel.setGravity(Gravity.CENTER);
        box.addView(loadingLabel, spaced(0, dp(14)));
        TextView tip = label("客户端界面已内置在本机，首次打开无需下载大文件。", 12, MUTED, false);
        tip.setGravity(Gravity.CENTER);
        box.addView(tip, spaced(0, dp(6)));
        loadingOverlay = box;
        root.addView(loadingOverlay, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
    }

    private void buildErrorOverlay() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setPadding(dp(30), dp(30), dp(30), dp(30));
        box.setBackgroundColor(BG);
        errorLabel = label("连不上服务器", 17, FG, true);
        errorLabel.setGravity(Gravity.CENTER);
        box.addView(errorLabel, spaced(0, dp(10)));
        TextView sub = label("请确认电脑上的 DSH 正在运行、手机网络可用后重试。", 13, MUTED, false);
        sub.setGravity(Gravity.CENTER);
        box.addView(sub, spaced(0, dp(18)));
        Button retry = new Button(this);
        retry.setText("重试");
        retry.setAllCaps(false);
        retry.setTextColor(Color.WHITE);
        retry.setBackground(rounded(ACCENT, dp(14)));
        retry.setOnClickListener(v -> {
            hideError();
            String target = startUrl();
            if (target == null) {
                showPairOverlay();
                return;
            }
            showLoading("正在重试…");
            web.loadUrl(target);
        });
        LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(dp(180), dp(48));
        box.addView(retry, rp);
        errorOverlay = box;
        errorOverlay.setVisibility(View.GONE);
        root.addView(errorOverlay, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
    }

    private void showLoading(String text) {
        if (loadingOverlay == null) {
            return;
        }
        if (loadingLabel != null) {
            loadingLabel.setText(text);
        }
        loadingOverlay.setVisibility(View.VISIBLE);
        if (errorOverlay != null) {
            errorOverlay.setVisibility(View.GONE);
        }
    }

    private void hideLoading() {
        if (loadingOverlay != null) {
            loadingOverlay.setVisibility(View.GONE);
        }
    }

    private void showError(String detail) {
        hideLoading();
        if (errorOverlay == null) {
            return;
        }
        if (errorLabel != null) {
            errorLabel.setText(detail == null || detail.isEmpty() ? "连不上服务器" : "连不上服务器\n" + detail);
        }
        errorOverlay.setVisibility(View.VISIBLE);
    }

    private void hideError() {
        if (errorOverlay != null) {
            errorOverlay.setVisibility(View.GONE);
        }
    }

    // ---------------------------------------------------------------- pairing

    /** Picks up a pairing link the phone was asked to open (browser, chat app, QR scanner). */
    private void handlePairIntent(Intent intent) {
        if (intent == null || intent.getData() == null) {
            return;
        }
        String url = normalizePairUrl(intent.getData().toString());
        if (url == null) {
            return;
        }
        pendingPairUrl = url;
        if (unlocked && web != null) {
            hidePairOverlay();
            loadStart();
        } else {
            toast("已收到配对链接，输入密码后自动配对");
        }
    }

    /**
     * Accepts a full pairing link or just the pairing code copied out of the desktop panel. Only
     * links on this relay's own domain are trusted, so no deep link can redirect the WebView.
     */
    private String normalizePairUrl(String raw) {
        return PairLinks.normalize(raw, siteUrl());
    }

    private void promptPairUrl() {
        final EditText input = plainField("粘贴配对链接或配对码");
        LinearLayout box = new LinearLayout(this);
        box.setPadding(dp(24), dp(8), dp(24), 0);
        box.addView(input, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        AlertDialog dlg = new AlertDialog.Builder(this)
                .setTitle("重新配对")
                .setMessage(siteUrl() == null
                        ? "把电脑「远程访问」面板里的完整配对链接发到这台手机，粘贴到这里。"
                        : "在电脑上打开 DSH →「远程访问」面板，复制配对链接发到手机，粘贴到这里。")
                .setView(box)
                .setPositiveButton("确定", null)
                .setNegativeButton("取消", null)
                .create();
        dlg.setOnShowListener(d -> dlg.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String url = normalizePairUrl(input.getText().toString());
                    if (url == null) {
                        input.setError(siteUrl() == null ? "需要完整的配对链接" : "链接格式不对");
                        return;
                    }
                    dlg.dismiss();
                    pendingPairUrl = url;
                    if (unlocked && web != null) {
                        hidePairOverlay();
                        loadStart();
                    } else {
                        toast("解锁后将自动完成配对");
                        showLock();
                    }
                }));
        dlg.show();
    }

    private void showPairOverlay() {
        if (pairOverlay == null) {
            buildPairOverlay();
        }
        if (loadingOverlay != null) {
            loadingOverlay.setVisibility(View.GONE);
        }
        if (errorOverlay != null) {
            errorOverlay.setVisibility(View.GONE);
        }
        if (pairField != null) {
            pairField.setText("");
        }
        pairOverlay.setVisibility(View.VISIBLE);
    }

    private void hidePairOverlay() {
        if (pairOverlay != null) {
            pairOverlay.setVisibility(View.GONE);
        }
    }

    private void buildPairOverlay() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER_HORIZONTAL);
        box.setPadding(dp(30), dp(48), dp(30), dp(48));
        scroll.addView(box, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        TextView title = label("连接你的电脑", 20, FG, true);
        title.setGravity(Gravity.CENTER);
        box.addView(title, spaced(0, dp(10)));

        TextView why = label(
                "这个 App 不绑定任何人的电脑，第一次使用需要和你的电脑配对一次。\n\n"
                        + "1. 在电脑上安装并开启 DSH 与「远程访问」插件\n"
                        + "2. 打开电脑上的「远程访问」面板，复制配对链接\n"
                        + "3. 把链接发到这台手机，粘贴到下面（或直接在手机上点开该链接）\n\n"
                        + "配对成功后本机记住你的电脑，以后打开直接进界面。",
                13, MUTED, false);
        why.setGravity(Gravity.CENTER);
        box.addView(why, spaced(0, dp(18)));

        pairField = plainField("粘贴配对链接（https://…/pair-accept?pair=…）");
        box.addView(pairField, fullWidth(spaced(0, dp(12))));

        Button pair = new Button(this);
        pair.setText("开始配对");
        pair.setTextSize(16);
        pair.setAllCaps(false);
        pair.setTextColor(Color.WHITE);
        pair.setBackground(rounded(ACCENT, dp(14)));
        pair.setOnClickListener(v -> {
            String url = normalizePairUrl(pairField.getText().toString());
            if (url == null) {
                pairField.setError("需要完整的配对链接");
                return;
            }
            pendingPairUrl = url;
            hidePairOverlay();
            loadStart();
        });
        LinearLayout.LayoutParams pairParams = fullWidth(spaced(0, dp(12)));
        pairParams.height = dp(50);
        box.addView(pair, pairParams);

        Button settings = new Button(this);
        settings.setText("设置 / 帮助");
        settings.setTextSize(13);
        settings.setAllCaps(false);
        settings.setTextColor(MUTED);
        settings.setBackgroundColor(Color.TRANSPARENT);
        settings.setOnClickListener(v -> openSettings());
        box.addView(settings, fullWidth(spaced(0, dp(4))));

        pairOverlay = scroll;
        pairOverlay.setVisibility(View.GONE);
        root.addView(pairOverlay, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
    }

    // ---------------------------------------------------------------- settings

    private void openSettings() {
        List<String> items = new ArrayList<>();
        items.add("重新加载界面（清空缓存重下）");
        items.add("修改进入密码");
        items.add("重新配对（粘贴配对链接）");
        items.add("复位：清除密码和配对");
        items.add("关于本应用");
        new AlertDialog.Builder(this)
                .setTitle("设置")
                .setItems(items.toArray(new String[0]), this::onSettingsChoice)
                .setNegativeButton("关闭", null)
                .show();
    }

    private void onSettingsChoice(DialogInterface dialog, int which) {
        switch (which) {
            case 0:
                if (!lock.hasPassword()) {
                    toast("请先设置密码");
                    return;
                }
                promptPassword("请输入密码以确认", () -> reloadForcing());
                break;
            case 1:
                promptPassword("请输入当前密码", () -> promptNewPassword());
                break;
            case 2:
                promptPairUrl();
                break;
            case 3:
                new AlertDialog.Builder(this)
                        .setTitle("复位本机")
                        .setMessage("将清除本机的密码、网页缓存和配对凭据。"
                                + "复位后必须用电脑上的配对链接重新配对，才能继续使用。")
                        .setPositiveButton("确定复位", (d, w) -> {
                            lock.clear();
                            lock.setCredentialRevoked(true);
                            CookieManager.getInstance().removeAllCookies(null);
                            CookieManager.getInstance().flush();
                            destroyWeb();
                            toast("已复位：请重设密码，然后重新配对");
                            showLock();
                        })
                        .setNegativeButton("取消", null)
                        .show();
                break;
            default:
                new AlertDialog.Builder(this)
                        .setTitle("关于")
                        .setMessage("DSH 手机版 · 配对版 1.0\n\n"
                                + "远程地址：" + (siteHost() == null ? "尚未配对" : siteHost()) + "\n"
                                + "本 App 只是一个带密码锁的壳：界面完全来自你自己的 DSH 服务，"
                                + "密码只在手机本地校验。\n\n"
                                + "安装包里不含任何人的配对凭据：第一次使用需要用你自己电脑上的"
                                + "配对链接配对一次，配对信息只保存在这台手机上。"
                                + "「复位」会清除密码与配对信息。")
                        .setPositiveButton("知道了", null)
                        .show();
        }
    }

    private interface Confirmed {
        void run();
    }

    private void promptPassword(String title, Confirmed onOk) {
        final EditText input = passwordField("密码");
        LinearLayout box = new LinearLayout(this);
        box.setPadding(dp(24), dp(8), dp(24), 0);
        box.addView(input, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        AlertDialog dlg = new AlertDialog.Builder(this)
                .setTitle(title)
                .setView(box)
                .setPositiveButton("确定", null)
                .setNegativeButton("取消", null)
                .create();
        dlg.setOnShowListener(d -> dlg.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            final String value = input.getText().toString();
            new Thread(() -> {
                final boolean ok = lock.verify(value);
                runOnUiThread(() -> {
                    if (ok) {
                        dlg.dismiss();
                        onOk.run();
                    } else {
                        input.setError("密码不正确");
                    }
                });
            }, "dsh-verify-settings").start();
        }));
        dlg.show();
    }

    private void promptNewPassword() {
        final EditText a = passwordField("新密码（至少 4 位）");
        final EditText b = passwordField("再输入一次");
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(24), dp(8), dp(24), 0);
        box.addView(a);
        box.addView(b);
        AlertDialog dlg = new AlertDialog.Builder(this)
                .setTitle("修改进入密码")
                .setView(box)
                .setPositiveButton("保存", null)
                .setNegativeButton("取消", null)
                .create();
        dlg.setOnShowListener(d -> dlg.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            String nv = a.getText().toString();
            if (nv.length() < 4) {
                a.setError("至少 4 位");
                return;
            }
            if (!nv.equals(b.getText().toString())) {
                b.setError("两次输入不一致");
                return;
            }
            lock.setPassword(nv);
            dlg.dismiss();
            toast("密码已更新");
        }));
        dlg.show();
    }

    // ---------------------------------------------------------------- lifecycle

    @Override
    protected void onStop() {
        super.onStop();
        CookieManager.getInstance().flush();
        if (suppressRelock) {
            suppressRelock = false;
            return;
        }
        backgroundedAt = SystemClock.elapsedRealtime();
    }

    @Override
    protected void onStart() {
        super.onStart();
        if (!unlocked) {
            return;
        }
        boolean away = backgroundedAt > 0
                && SystemClock.elapsedRealtime() - backgroundedAt >= RELOCK_GRACE_MS;
        backgroundedAt = 0;
        if (away) {
            showLock();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (web != null) {
            CookieManager.getInstance().flush();
        }
    }

    @Override
    public void onBackPressed() {
        if (!unlocked) {
            super.onBackPressed();
            return;
        }
        if (pairOverlay != null && pairOverlay.getVisibility() == View.VISIBLE) {
            // Back out of the pairing screen and ask for the password again.
            showLock();
            return;
        }
        if (web != null && web.canGoBack()) {
            web.goBack();
            return;
        }
        // At the root there is no browser chrome, so "settings" has to live here.
        new AlertDialog.Builder(this)
                .setTitle("DSH 手机版")
                .setItems(new String[]{"设置 / 帮助", "退出到桌面"}, (d, w) -> {
                    if (w == 0) {
                        openSettings();
                    } else {
                        moveTaskToBack(true);
                    }
                })
                .setNegativeButton("取消", null)
                .show();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode != REQ_FILE) {
            super.onActivityResult(requestCode, resultCode, data);
            return;
        }
        suppressRelock = false;
        if (fileCallback == null) {
            return;
        }
        Uri[] result = null;
        if (resultCode == RESULT_OK && data != null) {
            if (data.getClipData() != null) {
                int count = data.getClipData().getItemCount();
                result = new Uri[count];
                for (int i = 0; i < count; i++) {
                    result[i] = data.getClipData().getItemAt(i).getUri();
                }
            } else if (data.getData() != null) {
                result = new Uri[]{data.getData()};
            }
        }
        fileCallback.onReceiveValue(result);
        fileCallback = null;
    }

    // ---------------------------------------------------------------- small helpers

    private int dp(int value) {
        return Math.round(getResources().getDisplayMetrics().density * value);
    }

    private TextView label(String text, int sizeSp, int color, boolean bold) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextSize(sizeSp);
        tv.setTextColor(color);
        if (bold) {
            tv.setTypeface(Typeface.DEFAULT_BOLD);
        }
        return tv;
    }

    private EditText passwordField(String hint) {
        EditText field = new EditText(this);
        field.setHint(hint);
        field.setHintTextColor(MUTED);
        field.setTextColor(FG);
        field.setTextSize(17);
        field.setSingleLine(true);
        field.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        field.setBackground(roundedStroke(PANEL, ACCENT));
        field.setPadding(dp(16), dp(14), dp(16), dp(14));
        return field;
    }

    private EditText plainField(String hint) {
        EditText field = new EditText(this);
        field.setHint(hint);
        field.setHintTextColor(MUTED);
        field.setTextColor(FG);
        field.setTextSize(15);
        field.setSingleLine(true);
        field.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        field.setBackground(roundedStroke(PANEL, ACCENT));
        field.setPadding(dp(16), dp(14), dp(16), dp(14));
        return field;
    }

    private LinearLayout.LayoutParams fullWidth(LinearLayout.LayoutParams base) {
        base.width = ViewGroup.LayoutParams.MATCH_PARENT;
        return base;
    }

    private LinearLayout.LayoutParams spaced(int top, int bottom) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.topMargin = top;
        p.bottomMargin = bottom;
        return p;
    }

    private GradientDrawable rounded(int color, int radius) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(radius);
        return d;
    }

    private GradientDrawable roundedStroke(int color, int stroke) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(12));
        d.setStroke(dp(1), stroke);
        return d;
    }

    private void toast(String text) {
        Toast.makeText(this, text, Toast.LENGTH_SHORT).show();
    }
}
