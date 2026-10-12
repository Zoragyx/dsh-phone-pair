Adds one entry: `Zoragyx/dsh-phone-pair#dsh-phone-pair-kit` (category `remote`).

**What it does.** The phone half of this project is an Android app that pairs with a computer running DSH; this package is the computer half. Installing it enables the upstream pairing plugin [`@linxin666/dsh-remote-web-ui`](https://www.npmjs.com/package/@linxin666/dsh-remote-web-ui) through `cordis.patch.yml`, and turns on `autoTunnel: true` (a Cloudflare quick tunnel — no account, domain or extra binary needed) plus `relay: true` (the tunnel is registered under a fixed `<id>.dsh-market.com` subdomain, so the phone reconnects after a restart without scanning again). Its own `lib/index.js` registers no endpoints and writes one log line; everything else is the upstream plugin's behaviour.

**Please read the description as a functional requirement, not marketing.** The plugin is only half of a working setup: with the computer side installed and no phone app, there is nothing to pair with and the feature cannot be used at all. That is why both descriptions name the separate APK and link its download page — so the entry is not silently useless for someone who installs only the computer half.

**Checklist against `contributing.md`**

- `dsh.bundle` manifest — `plugin/dsh-phone-pair-kit/package.json` → `"dsh": { "bundle": { "patch": "./cordis.patch.yml" } }`, with `cordis.patch.yml` next to it.
- Real, working code — the package is small on purpose: it composes configuration instead of shipping behaviour of its own. The app, its tests, and the build/verification tooling live in `android/`, and the paired path was verified end to end from the public internet (pairing, cookie, bundled assets) — see `HANDOFF.md`.
- Repository age — the repository was created 2026-10-10 and is older than one day when this PR is opened.
- `dsh-plugin` topic — set on the repository.
- Dependency points upstream — `dependencies` resolves to the author's published npm package `@linxin666/dsh-remote-web-ui` (rule 8); none of the upstream source is vendored, and `NOTICE.md` credits it explicitly.
- Prebuilt `tarball` — the entry declares a `.tgz` built with `npm pack`
  (`dsh-phone-pair-kit.tgz`, unversioned so `releases/latest/download/` keeps working). The catalog's
  default `github:` install needs git on the user's machine, which many people do not have; the
  tarball makes the one-click install work without it.
- One entry per PR — this PR touches exactly one file, `data/plugins/Zoragyx__dsh-phone-pair--plugin-dsh-phone-pair-kit.yml`, and nothing else.

I am happy to adjust the wording, the category, or the shape of the entry — just say what you would prefer.
