# Compatibility evidence implementation plan

Goal: complete roadmap v0.6.0 with reproducible fixtures, an explicit evidence
matrix and an isolated native Excel round trip where available.

Architecture: synthetic extended-probe corpus generated as deterministic bytes,
with literal expected outcomes and SHA-256 metadata. Native Excel profiles use
a separate automation instance, synthetic input only, disabled macros/alerts,
fixed CSV delimiter and either text-column import or automatic inference.
Export CSV data only, close the owned workbook/application, retain version and
profile evidence without usernames or machine paths. CI consumes checked-in
fixtures without requiring Office.

Review focus: expected outcomes independent of the comparator, exact newline
bytes across platforms, native-output provenance, formula-literal safety in the
text profile, deterministic rebuilds, no modification of existing workbooks,
no customer data or local paths in public fixtures.

1. Write failing corpus tests for generation, exact recorded issue IDs/codes,
   fixture hashes and deterministic rebuilds; implement tools/compatibility.py.
2. Add a reusable native Excel script with exclusive outputs and reliable COM
   cleanup. Run text and automatic profiles against synthetic extended probes;
   inspect actual differences, record exact Excel version and observed results.
3. Package the corpus and docs, clearly distinguish synthetic parser evidence
   from the native Excel observations. Google Sheets/LibreOffice remain untested.
4. Focused/full tests, independent review, release gates and trail check;
   commit/push, all hosted jobs, publish/verify v0.6.0 separately.
