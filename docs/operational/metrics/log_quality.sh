#!/usr/bin/env bash
set -euo pipefail
TAIL="${TAIL:-5000}"
SERVICE="${SERVICE:-backend-consumer}"

ei=$(docker-compose logs --tail="$TAIL" "$SERVICE" | grep -Ewc '\bevent_indexed\b' || true)
vf=$(docker-compose logs --tail="$TAIL" "$SERVICE" | grep -Ewc '\bvalidation_failed\b' || true)
pf=$(docker-compose logs --tail="$TAIL" "$SERVICE" | grep -Ewc '\bprocessing_failed\b' || true)

total=$((ei + vf + pf))
ratio_ok="n/a"
if [ "$total" -gt 0 ]; then
  ratio_ok=$(awk -v a="$ei" -v b="$total" 'BEGIN{printf "%.2f%%", (a*100)/b}')
fi

echo "event_indexed:      $ei"
echo "validation_failed:  $vf"
echo "processing_failed:  $pf"
echo "success_ratio:      $ratio_ok (last $TAIL log lines)"