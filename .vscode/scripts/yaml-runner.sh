#!/usr/bin/env bash
set -Eeuo pipefail

# Simple YAML runner for .vscode/commands/*.yaml
# Supports: execution.shell, execution.workingDirectory, execution.env, steps[].run, steps[].negate

YAML_FILE=${1:-".vscode/commands/startup.yaml"}

if [[ ! -f "$YAML_FILE" ]]; then
  echo "YAML file not found: $YAML_FILE" >&2
  exit 1
fi

if command -v yq >/dev/null 2>&1; then
  SHELL_NAME=$(yq -r '.execution.shell // "bash"' "$YAML_FILE")
  WORKDIR=$(yq -r '.execution.workingDirectory // "."' "$YAML_FILE")
  STOP_ON_ERROR=$(yq -r '.execution.stopOnError // true' "$YAML_FILE")
  # Export env vars
  mapfile -t ENV_KEYS < <(yq -r '.execution.env | keys[]?' "$YAML_FILE") || true
  for k in "${ENV_KEYS[@]:-}"; do
    v=$(yq -r ".execution.env[\"$k\"]" "$YAML_FILE")
    export "$k"="$v"
  done

  cd "$WORKDIR"

  COUNT=$(yq -r '.steps | length' "$YAML_FILE")
  for ((i=0; i<COUNT; i++)); do
    CMD=$(yq -r ".steps[$i].run" "$YAML_FILE")
    NEGATE=$(yq -r ".steps[$i].negate // false" "$YAML_FILE")
    [[ "$CMD" == "null" ]] && continue
    if [[ "$NEGATE" == "true" ]]; then
      echo "[skip] $CMD"
      continue
    fi
    echo "+ $CMD"
    if [[ "$SHELL_NAME" == "bash" ]]; then
      bash -lc "$CMD"; rc=$?
    else
      "$SHELL_NAME" -lc "$CMD"; rc=$?
    fi
    if [[ $rc -ne 0 ]]; then
      echo "[fail:$rc] $CMD"
      if [[ "$STOP_ON_ERROR" == "true" ]]; then
        exit $rc
      fi
    fi
  done
  exit 0
fi

# Fallback parser if yq not available (assumes simple YAML formatting)
SHELL_NAME=$(awk -F': ' '/^\s*shell:/ {print $2}' "$YAML_FILE" | tr -d '"')
SHELL_NAME=${SHELL_NAME:-bash}
WORKDIR=$(awk -F': ' '/^\s*workingDirectory:/ {print $2}' "$YAML_FILE" | tr -d '"')
WORKDIR=${WORKDIR:-.}
STOP_ON_ERROR=$(awk -F': ' '/^\s*stopOnError:/ {print $2}' "$YAML_FILE" | tr -d '"')
STOP_ON_ERROR=${STOP_ON_ERROR:-true}
cd "$WORKDIR"

awk '
  BEGIN{insteps=0}
  /^steps:/ {insteps=1; next}
  insteps==1 && /^\s*-\s+run:/ {
    cmd=$0; sub(/^\s*-\s+run:\s+/,"",cmd); gsub(/^\"|\"$/,"",cmd);
    getline; neg=0; if($0 ~ /negate:\s+true/) neg=1;
    print neg "\t" cmd
  }
' "$YAML_FILE" | while IFS=$'\t' read -r neg cmd; do
  if [[ "$neg" == "1" ]]; then
    echo "[skip] $cmd"
    continue
  fi
  echo "+ $cmd"
  if [[ "$SHELL_NAME" == "bash" ]]; then
    bash -lc "$cmd"; rc=$?
  else
    "$SHELL_NAME" -lc "$cmd"; rc=$?
  fi
  if [[ $rc -ne 0 ]]; then
    echo "[fail:$rc] $cmd"
    if [[ "$STOP_ON_ERROR" == "true" ]]; then
      exit $rc
    fi
  fi
done
