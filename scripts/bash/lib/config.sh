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

# Limits
export MAX_FILE_SIZE=$((1024 * 1024)) # 1MB
