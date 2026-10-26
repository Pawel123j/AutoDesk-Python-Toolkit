import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

// A temporary, tested source patch, not an ignored vulnerability. Any change to
// the advisory, installed code, version, or review deadline fails this gate.
const patchedAdvisory = 'https://github.com/advisories/GHSA-vfj7-8cjw-p6xm';
const reviewBefore = '2026-11-18';
const patchedParserSha256 = '0d010535667c2889449adcc0cf596c2db2c61f73c513b96c4a2cf1fd8ad1e018';
const require = createRequire(import.meta.url);
const npmCli = process.env.npm_execpath;
const audit = spawnSync(npmCli ? process.execPath : 'npm', npmCli ? [npmCli, 'audit', '--json'] : ['audit', '--json'], {
  encoding: 'utf8', timeout: 120000, maxBuffer: 8 * 1024 * 1024, shell: false,
});
if (audit.error || audit.status > 1 || !audit.stdout) throw new Error('npm audit unavailable; security check fails closed');
const report = JSON.parse(audit.stdout);
if (report.error || !report.vulnerabilities) throw new Error('Invalid npm audit report');
const checked = new Set();
function verifyPatchedBraces(node) {
  if (checked.has(node)) return;
  assert.ok(new Date().toISOString().slice(0, 10) < reviewBefore, 'braces patch needs upstream review');
  const packagePath = join(process.cwd(), node, 'package.json');
  const pkg = JSON.parse(readFileSync(packagePath, 'utf8'));
  assert.equal(pkg.name, 'braces');
  assert.equal(pkg.version, '3.0.3');
  const parser = readFileSync(join(dirname(packagePath), 'lib/parse.js'));
  assert.equal(createHash('sha256').update(parser).digest('hex'), patchedParserSha256, 'Missing or changed nesting-limit patch');
  const braces = require(dirname(packagePath));
  assert.deepEqual(braces.expand('src/{app,components}/**/*.{ts,tsx}'), [
    'src/app/**/*.ts', 'src/app/**/*.tsx', 'src/components/**/*.ts', 'src/components/**/*.tsx',
  ]);
  assert.deepEqual(braces.expand('v{1..3}'), ['v1', 'v2', 'v3']);
  for (const [open, close] of [['{', '}'], ['(', ')'], ['{(', ')}']]) {
    for (const depth of [129, 4000, 10000]) {
      for (const ending of [close.repeat(depth), '']) {
        const pattern = open.repeat(depth) + 'a,b' + ending;
        for (const method of ['parse', 'compile', 'expand', 'stringify']) {
          assert.throws(() => braces[method](pattern), (error) => error instanceof SyntaxError && /nesting|max characters/.test(error.message));
        }
      }
    }
  }
  // Escaped delimiters, quoted text and many shallow groups remain valid.
  assert.ok(braces.compile('\\{literal\\}'));
  assert.ok(braces.compile('"' + '{'.repeat(1000) + '"'));
  assert.ok(braces.compile('{a,b}'.repeat(1000)));
  checked.add(node);
}
// Verify the committed patch even if the advisory feed no longer reports it.
// Otherwise a zero-finding audit could conceal a missing or modified patch.
verifyPatchedBraces('node_modules/braces');
const failures = [];
for (const vulnerability of Object.values(report.vulnerabilities)) {
  for (const advisory of vulnerability.via) {
    if (typeof advisory !== 'object' || !['high', 'critical'].includes(advisory.severity)) continue;
    if (advisory.url === patchedAdvisory && vulnerability.name === 'braces' && vulnerability.nodes.length) {
      for (const node of vulnerability.nodes) verifyPatchedBraces(node);
    } else failures.push(`${advisory.severity}: ${advisory.name}: ${advisory.url}`);
  }
}
if (failures.length) throw new Error('Unmitigated audit findings:\n' + [...new Set(failures)].join('\n'));
console.log(`Security gate PASS: ${checked.size} braces installation(s) verified and attack regressions passed; no other high/critical advisories.`);
console.log('Raw npm audit counts (include patched dependencies):', report.metadata?.vulnerabilities);
