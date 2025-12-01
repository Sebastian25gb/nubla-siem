#!/usr/bin/env bash
#
# ISM + Alias healthcheck and safe remediation script
# - Reads tenants from config/tenants.json (expects format {"tenants":[{ "id": "...", "policy_id": "...", ... }, ...]})
# - For each tenant ensures alias logs-<id> has exactly one write index
# - For the write index checks ISM explain and attempts remediation (settings + remove/add policy)
#
# Usage:
#   ./backend/scripts/ism_healthcheck.sh         # dry-run (no changes)
#   ./backend/scripts/ism_healthcheck.sh --yes   # perform remediation actions
#   ./backend/scripts/ism_healthcheck.sh --yes --force-delete  # allow deleting empty, broken indices (dangerous)
#
set -euo pipefail
SCRIPT_NAME=$(basename "$0")
OPENSEARCH_HOST="${OPENSEARCH_HOST:-http://localhost:9201}"
OS_USER="${OS_USER:-admin}"
OS_PASS="${OS_PASS:-admin}"
TENANTS_FILE="${TENANTS_FILE:-config/tenants.json}"
DRY_RUN=true
FORCE_DELETE=false

log() { printf '%s %s\n' "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')]" "$*"; }

usage() {
  cat <<EOF
$SCRIPT_NAME [--yes] [--force-delete] [--tenants-file PATH]
  --yes          : actually perform remediation (default: dry-run)
  --force-delete : allow deleting empty, irrecoverable indices (use with caution)
  --tenants-file : override tenants json path (default: $TENANTS_FILE)
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes) DRY_RUN=false; shift ;;
    --force-delete) FORCE_DELETE=true; shift ;;
    --tenants-file) TENANTS_FILE="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

if [[ ! -f "$TENANTS_FILE" ]]; then
  log "ERROR: tenants file not found: $TENANTS_FILE"
  exit 2
fi

# jq needs to be available
if ! command -v jq >/dev/null 2>&1; then
  log "ERROR: jq is required"
  exit 2
fi

# read tenants list in form of array of objects
TENANTS_JSON=$(jq -c '.tenants[]' "$TENANTS_FILE" 2>/dev/null) || {
  log "ERROR: failed to parse tenants file or no tenants[] present"
  exit 2
}

curl_base=(curl -s -u "${OS_USER}:${OS_PASS}")

for t in $TENANTS_JSON; do
  tid=$(jq -r '.id' <<<"$t")
  policy_id=$(jq -r '.policy_id // empty' <<<"$t")
  alias="logs-${tid}"
  log "CHECK: tenant=${tid} alias=${alias} policy=${policy_id:-(none)}"

  # fetch alias mappings
  alias_resp=$("${curl_base[@]}" "${OPENSEARCH_HOST}/_alias/${alias}" || true)
  if [[ -z "$alias_resp" ]]; then
    log "WARN: unable to fetch alias ${alias} (empty response). Skipping tenant=${tid}"
    continue
  fi

  # determine write indices (is_write_index == true)
  write_indices=$(jq -r "to_entries[] | select(.value.aliases.\"${alias}\" != null) | select(.value.aliases.\"${alias}\".is_write_index==true) | .key" <<<"$alias_resp" || true)
  write_count=$(wc -w <<<"$write_indices" | tr -d ' ')
  if [[ -z "$write_indices" ]]; then write_count=0; fi

  if (( write_count != 1 )); then
    log "ALIAS ISSUE: alias=${alias} has write_count=${write_count}"
    log "Existing indices for alias:"
    jq -r 'to_entries[] | .key + " -> " + ( .value.aliases | tostring )' <<<"$alias_resp" | sed -e 's/^/  /'
    # remediation: pick latest index by name as candidate write index
    candidate=$(jq -r 'to_entries[] | .key' <<<"$alias_resp" | sort -V | tail -n1 || true)
    if [[ -z "$candidate" ]]; then
      log "No candidate index found for alias=${alias} — skipping"
      continue
    fi
    log "Remediation plan: set ${candidate} as write-index and unset others"
    actions='{"actions":['
    first=true
    for idx in $(jq -r 'to_entries[] | .key' <<<"$alias_resp"); do
      is_write="false"
      if [[ "$idx" == "$candidate" ]]; then is_write="true"; fi
      if [[ "$first" == true ]]; then first=false; else actions+=", "; fi
      actions+="{\"add\":{\"index\":\"$idx\",\"alias\":\"$alias\",\"is_write_index\":$is_write}}"
    done
    actions+='] }'
    log "Alias actions: $actions"
    if [[ "$DRY_RUN" == true ]]; then
      log "DRY-RUN: would POST /_aliases with actions above"
    else
      log "Executing alias normalization for ${alias}"
      echo "$actions" | "${curl_base[@]}" -XPOST "${OPENSEARCH_HOST}/_aliases" -H 'Content-Type: application/json' | jq . || log "Alias normalization request failed"
    fi
  else
    candidate=$(head -n1 <<<"$write_indices")
    log "Alias OK: alias=${alias} write_index=${candidate}"
  fi

  # Now inspect ISM explain for candidate (write index)
  if [[ -z "$candidate" ]]; then
    log "No write index candidate for alias ${alias} — skipping ISM check"
    continue
  fi

  explain_raw=$("${curl_base[@]}" "${OPENSEARCH_HOST}/_plugins/_ism/explain/${candidate}" || true)
  if [[ -z "$explain_raw" ]]; then
    log "WARN: empty explain for index ${candidate}"
    continue
  fi

  enabled=$(jq -r ".[\"${candidate}\"].enabled // \"null\"" <<<"$explain_raw")
  info_msg=$(jq -r ".[\"${candidate}\"].info.message // \"\" " <<<"$explain_raw" | tr -d '\n')
  policy_assigned=$(jq -r ".[\"${candidate}\"].policy_id // .[\"${candidate}\"].\"index.plugins.index_state_management.policy_id\" // empty" <<<"$explain_raw")

  log "ISM: index=${candidate} enabled=${enabled} policy=${policy_assigned:-(none)} info='${info_msg}'"

  need_remediate=false
  if [[ "$enabled" != "true" ]]; then
    need_remediate=true
  fi
  if [[ "$info_msg" =~ Missing ]]; then
    need_remediate=true
  fi

  if [[ "$need_remediate" == true ]]; then
    log "Remediation needed for index=${candidate} (enabled=${enabled} info='${info_msg}')"

    # 1) set settings rollover_alias + auto_manage
    settings_payload=$(cat <<JSON
{
  "index": {
    "opendistro.index_state_management.rollover_alias": "${alias}",
    "opendistro.index_state_management.auto_manage": true,
    "index.plugins.index_state_management.rollover_alias": "${alias}",
    "index.plugins.index_state_management.auto_manage": true
  }
}
JSON
)
    # use -d with curl (or --data-binary @- if piping); previous bug was missing -d
    log "Settings payload: (short) $(jq -c . <<<"$settings_payload")"
    if [[ "$DRY_RUN" == true ]]; then
      log "DRY-RUN: would PUT /${candidate}/_settings"
    else
      "${curl_base[@]}" -XPUT "${OPENSEARCH_HOST}/${candidate}/_settings" -H 'Content-Type: application/json' -d "$settings_payload" | jq . || log "Failed to update settings for ${candidate}"
    fi

    # 2) remove policy (idempotent)
    if [[ "$DRY_RUN" == true ]]; then
      log "DRY-RUN: would POST /_plugins/_ism/remove/${candidate}"
    else
      "${curl_base[@]}" -XPOST "${OPENSEARCH_HOST}/_plugins/_ism/remove/${candidate}" | jq . || log "Failed remove policy for ${candidate}"
    fi

    # 3) add policy back if we have policy_id in tenants config
    if [[ -n "$policy_id" && "$policy_id" != "null" ]]; then
      add_payload="{\"policy_id\":\"${policy_id}\"}"
      if [[ "$DRY_RUN" == true ]]; then
        log "DRY-RUN: would POST /_plugins/_ism/add/${candidate} payload=${add_payload}"
      else
        "${curl_base[@]}" -XPOST "${OPENSEARCH_HOST}/_plugins/_ism/add/${candidate}" -H 'Content-Type: application/json' -d "$add_payload" | jq . || log "Failed add policy for ${candidate}"
      fi
    else
      log "No policy_id provided for tenant ${tid}; skipped attach"
    fi

    # Re-check explain after small wait
    if [[ "$DRY_RUN" == false ]]; then
      sleep 2
      new_explain=$("${curl_base[@]}" "${OPENSEARCH_HOST}/_plugins/_ism/explain/${candidate}" || true)
      log "Post-remediation explain: $(jq -c . <<<"$new_explain")"
    fi
  else
    log "ISM OK for index=${candidate}"
  fi
done

log "ISM healthcheck completed (dry_run=${DRY_RUN})"
exit 0