#!/usr/bin/env bash

# Configuration for SpecKit

# Directory Names
export SPECS_DIR_NAME="specs"
export TEMPLATES_DIR_NAME="templates"

# File Names
export SPEC_TEMPLATE_NAME="spec-template.md"
export AGENT_TEMPLATE_NAME="agent-file-template.md"
export PLAN_FILE_NAME="plan.md"

# Agent File Paths (Relative to Repo Root)
export CLAUDE_FILE_PATH="CLAUDE.md"
export GEMINI_FILE_PATH="GEMINI.md"
export COPILOT_FILE_PATH=".github/copilot-instructions.md"
export CURSOR_FILE_PATH=".cursor/rules/specify-rules.mdc"
export QWEN_FILE_PATH="QWEN.md"
export AGENTS_FILE_PATH="AGENTS.md"
export WINDSURF_FILE_PATH=".windsurf/rules/specify-rules.md"

# Agent Definitions
# shellcheck disable=SC2034 # Used by other scripts
declare -Ax SPECKIT_AGENTS_FILES
SPECKIT_AGENTS_FILES["claude"]="$CLAUDE_FILE_PATH"
SPECKIT_AGENTS_FILES["gemini"]="$GEMINI_FILE_PATH"
SPECKIT_AGENTS_FILES["copilot"]="$COPILOT_FILE_PATH"
SPECKIT_AGENTS_FILES["cursor"]="$CURSOR_FILE_PATH"
SPECKIT_AGENTS_FILES["qwen"]="$QWEN_FILE_PATH"
SPECKIT_AGENTS_FILES["opencode"]="$AGENTS_FILE_PATH"
SPECKIT_AGENTS_FILES["codex"]="$AGENTS_FILE_PATH"
SPECKIT_AGENTS_FILES["windsurf"]="$WINDSURF_FILE_PATH"

# shellcheck disable=SC2034 # Used by other scripts
declare -Ax SPECKIT_AGENTS_NAMES
SPECKIT_AGENTS_NAMES["claude"]="Claude Code"
SPECKIT_AGENTS_NAMES["gemini"]="Gemini CLI"
SPECKIT_AGENTS_NAMES["copilot"]="GitHub Copilot"
SPECKIT_AGENTS_NAMES["cursor"]="Cursor IDE"
SPECKIT_AGENTS_NAMES["qwen"]="Qwen Code"
SPECKIT_AGENTS_NAMES["opencode"]="opencode"
SPECKIT_AGENTS_NAMES["codex"]="Codex CLI"
SPECKIT_AGENTS_NAMES["windsurf"]="Windsurf"

# Limits
export MAX_FILE_SIZE=$((1024 * 1024)) # 1MB
