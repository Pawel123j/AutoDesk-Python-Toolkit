# Temporary dependency security patch

`braces@3.0.3` has no patched release for GHSA-vfj7-8cjw-p6xm in the registry at validation time (2026-10-18). Its parser now rejects AST nesting beyond 128 levels, including braces and parentheses, before recursive compilation/stringification/expansion. Normal glob expansion and ranges remain supported. Untrusted prebuilt AST objects are outside the string-pattern API used by these build tools.

`npm ci` applies the versioned patch with `patch-package --error-on-fail`. `npm run security:check` queries the full npm audit, verifies the installed parser SHA-256 and version for **every reported braces installation**, runs deeply nested/unfinished/mixed pattern regressions plus valid pattern checks, and fails on any other high/critical advisory or unavailable audit. This exact advisory is considered mitigated only with that evidence. Raw `npm audit` still reports it; do not describe the raw audit as zero findings.

The exception expires on **2026-11-18** and must be reviewed against upstream. Remove the patch and exception when a compatible fixed release is available. The gate also fails if the patch is absent, modified, or applied to another version. Moderate selector-parser issues are addressed with 7.1.6 and the production build/E2E verify compatibility.
