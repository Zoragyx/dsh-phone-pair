/**
 * Validates the phone pairing kit without installing it into a live DSH profile.
 *
 * <pre>
 *   node tools/validate_kit.mjs
 *   node tools/validate_kit.mjs --profile-patch "%DSH_PROFILE_DIR%\cordis.patch.yml"
 * </pre>
 *
 * It checks the three things that make a bundle plugin loadable - `package.json` metadata, the
 * patch file the loader merges, and the host half's exports - and, because a duplicate plugin id
 * makes the loader fail, it can also scan a real profile patch for an existing `remote-web-ui`
 * entry. Nothing is written and no DSH process is started.
 */
import { existsSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const kitDir = resolve(here, '..', 'plugin', 'dsh-phone-pair-kit')

const require = createRequire(import.meta.url)
let yaml = null
for (const candidate of [
    'C:/Users/Zora/.dsh/profiles/desktop/node_modules/js-yaml',
    'js-yaml',
]) {
    try {
        yaml = require(candidate)
        break
    } catch {
        // try the next one
    }
}

let passed = 0
let failed = 0
const eq = (name, expected, actual) => {
    const ok = expected === actual
    ok ? passed++ : failed++
    if (!ok) console.log(`FAIL ${name}\n  expected: ${expected}\n  actual:   ${actual}`)
}
const ok = (name, condition, detail) => {
    condition ? passed++ : failed++
    if (!condition) console.log(`FAIL ${name}${detail ? `\n  ${detail}` : ''}`)
}

const argOf = (flag) => {
    const index = process.argv.indexOf(flag)
    return index >= 0 ? process.argv[index + 1] : null
}

// ------------------------------------------------------------------ package.json
const pkgPath = join(kitDir, 'package.json')
ok('package.json exists', existsSync(pkgPath), pkgPath)
const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'))
eq('package name', 'dsh-phone-pair-kit', pkg.name)
eq('package type', 'module', pkg.type)
eq('main entry', 'lib/index.js', pkg.main)
eq('bundle patch', './cordis.patch.yml', pkg.dsh?.bundle?.patch)
ok('declares the relay plugin as a dependency',
    typeof pkg.dependencies?.['@linxin666/dsh-remote-web-ui'] === 'string',
    JSON.stringify(pkg.dependencies))
for (const file of ['lib', 'cordis.patch.yml', 'README.md']) {
    ok(`files[] ships ${file}`, (pkg.files ?? []).includes(file), JSON.stringify(pkg.files))
}
ok('main entry exists on disk', existsSync(join(kitDir, pkg.main)), join(kitDir, pkg.main))
ok('patch file exists on disk', existsSync(join(kitDir, 'cordis.patch.yml')))

// ------------------------------------------------------------------ patch file
const patchText = readFileSync(join(kitDir, 'cordis.patch.yml'), 'utf8')
if (yaml) {
    let patch = null
    try {
        patch = yaml.load(patchText)
    } catch (error) {
        failed++
        console.log(`FAIL patch parses as YAML\n  ${error.message}`)
    }
    if (patch) {
        ok('patch is a list', Array.isArray(patch), JSON.stringify(patch))
        const inserts = (patch ?? []).filter((entry) => entry && typeof entry === 'object' && 'insert' in entry)
        eq('exactly one insert block', 1, inserts.length)
        const entries = (inserts[0]?.insert ?? []).filter(
            (entry) => entry && typeof entry === 'object' && entry.id === 'remote-web-ui')
        eq('one remote-web-ui entry', 1, entries.length)
        const entry = entries[0] ?? {}
        eq('inserts the published plugin name', '@linxin666/dsh-remote-web-ui', entry.name)
        eq('autoTunnel is on', true, entry.config?.autoTunnel)
        eq('relay is on', true, entry.config?.relay)
        ok('insert entry only carries id/name/config',
            Object.keys(entry).every((key) => ['id', 'name', 'config'].includes(key)),
            JSON.stringify(Object.keys(entry)))
    }
} else {
    console.log('note: js-yaml not found - patch YAML was only scanned as text')
    ok('patch inserts remote-web-ui', /id:\s*remote-web-ui/.test(patchText))
    ok('patch turns autoTunnel on', /autoTunnel:\s*true/.test(patchText))
    ok('patch turns relay on', /relay:\s*true/.test(patchText))
}

// ------------------------------------------------------------------ host half
const module_ = await import(pathToFileURL(join(kitDir, pkg.main)).href)
eq('exports a name', 'dsh-phone-pair-kit', module_.name)
ok('exports inject as an array', Array.isArray(module_.inject), JSON.stringify(module_.inject))
ok('exports apply as a function', typeof module_.apply === 'function')

if (typeof module_.apply === 'function') {
    const lines = []
    const ctx = { logger: { info: (message) => lines.push(message) } }
    let threw = null
    try {
        module_.apply(ctx)
        eq('apply() logs once', 1, lines.length)
        ok('log line mentions the kit', lines[0]?.includes('dsh-phone-pair-kit'), lines[0])
        for (const [name, bad] of [
            ['apply(undefined)', undefined],
            ['apply({})', {}],
            ['apply({ logger: {} })', { logger: {} }],
        ]) {
            try {
                module_.apply(bad)
                passed++
            } catch (error) {
                failed++
                console.log(`FAIL ${name} must not throw\n  ${error.message}`)
            }
        }
    } catch (error) {
        threw = error
        failed++
        console.log(`FAIL apply() threw\n  ${error.stack ?? error.message}`)
    }
    void threw
}

// ------------------------------------------------------------------ profile patch (duplicate id)
const profilePatch = argOf('--profile-patch')
if (profilePatch) {
    if (!existsSync(profilePatch)) {
        console.log(`note: profile patch not found: ${profilePatch}`)
    } else {
        const text = readFileSync(profilePatch, 'utf8')
        const lines = text.split(/\r?\n/)
        const hits = []
        lines.forEach((line, index) => {
            if (/^\s*-\s*id:\s*remote-web-ui\s*$/.test(line)) hits.push(index + 1)
        })
        console.log(`profile patch: ${profilePatch}`)
        console.log(hits.length
            ? `note: remote-web-ui already configured at line(s) ${hits.join(', ')} - remove that entry before adding this kit, or two entries for the same plugin id will fail to load`
            : 'note: no remote-web-ui entry in this profile patch - installing this kit adds the first one')
    }
}

console.log(`kit checks: passed=${passed} failed=${failed}`)
if (failed > 0) process.exit(1)
