//#region src/index.ts
/**
 * Host half of the phone pairing kit.
 *
 * The kit itself has no endpoints: it exists so that installing one plugin turns a DSH computer
 * into a pairable host. `cordis.patch.yml` inserts `@linxin666/dsh-remote-web-ui` with
 * `autoTunnel: true` + `relay: true`, which is the whole server side of the phone flow
 * (`/pair-accept?pair=<code>`, `/pair-app`, revocable per-device sessions).
 */
/** Cordis plugin name. */
const name = 'dsh-phone-pair-kit';
/** No host services are provided or required. */
const inject = [];
/**
 * Nothing to wire up on the host: the pairing routes belong to remote-web-ui. The optional log line
 * only runs if this DSH build exposes a logger, so a missing one can never fail the plugin.
 */
function apply(ctx) {
    const info = ctx && ctx.logger && ctx.logger.info;
    if (typeof info === 'function') {
        info.call(ctx.logger, '[dsh-phone-pair-kit] 配对后端已启用：remote-web-ui（自动隧道 + 固定中继域名）。打开「远程访问」复制配对链接，粘到手机 App 即可。');
    }
}
//#endregion
export { apply, inject, name };
