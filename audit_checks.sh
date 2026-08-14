#!/usr/bin/env bash
set +e
cd "$(dirname "$(readlink -f "$0")")"
: > audit_test_results.txt
run() {
  label="$1"
  shift
  printf '\n--- %s ---\n' "$label" >> audit_test_results.txt
  "$@" >> audit_test_results.txt 2>&1
  code=$?
  printf '%s_EXIT=%s\n' "$label" "$code" >> audit_test_results.txt
}
run PYTEST python3 -m pytest -q -p no:cacheprovider --timeout=120
run SELFCHECK python3 scripts/selfcheck.py
printf '\n--- JS ---\n' >> audit_test_results.txt
js_failed=0
while IFS= read -r -d '' f; do
  node --check "$f" >> audit_test_results.txt 2>&1
  code=$?
  if [ "$code" -ne 0 ]; then
    printf 'JS_FILE_FAIL=%s CODE=%s\n' "$f" "$code" >> audit_test_results.txt
    js_failed=1
  fi
done < <(find miniapp/js admin -type f -name '*.js' -print0)
printf 'JS_EXIT=%s\n' "$js_failed" >> audit_test_results.txt
run DESIGN python3 scripts/check_design_contract.py
run RELEASE python3 scripts/release_gate.py
cat audit_test_results.txt
exit $((js_failed))
