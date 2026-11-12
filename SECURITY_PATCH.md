# Temporary dependency security patch

`braces@3.0.3` has no patched release for GHSA-vfj7-8cjw-p6xm in the registry at validation time (2026-10-18). Its parser now rejects AST nesting beyond 128 levels, including braces and parentheses, before recursive compilation/stringification/expansion. Normal glob expansion and ranges remain supported. Untrusted prebuilt AST objects are outside the string-pattern API used by these build tools.

`npm ci` applies the versioned patch with `patch-package --error-on-fail`. `npm run security:check` queries the full npm audit, always verifies the primary braces parser SHA-256 and version even when the advisory feed has no findings, verifies **every additional reported braces installation**, runs deeply nested/unfinished/mixed pattern regressions plus valid pattern checks, and fails on any other advisory, regardless of severity, or unavailable audit. This exact advisory is considered mitigated only with that evidence. Raw audit findings depend on the current advisory feed; always report that result separately from verification of the installed patch.

The exception expires on **2026-11-18** and must be reviewed against upstream. Remove the patch and exception when a compatible fixed release is available. The gate also fails if the patch is absent, modified, or applied to another version. Moderate selector-parser issues are addressed with 7.1.6 and the production build/E2E verify compatibility.

`@typescript-eslint/typescript-estree` uses a targeted override of `minimatch` to
11.0.8 for GHSA-g3hv-75wg-m249. As of 2026-11-12, the latest typescript-eslint
8.72.2 still selects the affected minimatch 10 series. Only this caller is
overridden; ESLint's separate minimatch 3 installation is unaffected by that
advisory and remains unchanged. Node 24 satisfies the patched package's runtime
requirement. Lint, type checking and the production build exercise the upgraded
toolchain; remove the override once the caller selects a patched version itself.
