function Get-SpecKitConfig {
    return @{
        # Directory Names
        SPECS_DIR_NAME       = 'specs'
        TEMPLATES_DIR_NAME   = 'templates'

        # File Names
        SPEC_TEMPLATE_NAME   = 'spec-template.md'
        AGENT_TEMPLATE_NAME  = 'agent-file-template.md'
        PLAN_FILE_NAME       = 'plan.md'

        # Agent File Paths (Relative to Repo Root)
        CLAUDE_FILE_PATH     = 'CLAUDE.md'
        GEMINI_FILE_PATH     = 'GEMINI.md'
        COPILOT_FILE_PATH    = '.github/copilot-instructions.md'
        CURSOR_FILE_PATH     = '.cursor/rules/specify-rules.mdc'
        QWEN_FILE_PATH       = 'QWEN.md'
        AGENTS_FILE_PATH     = 'AGENTS.md'
        WINDSURF_FILE_PATH   = '.windsurf/rules/specify-rules.md'

        # Agent Definitions
        Agents = @{
            claude   = @{ File = 'CLAUDE.md'; Name = 'Claude Code' }
            gemini   = @{ File = 'GEMINI.md'; Name = 'Gemini CLI' }
            copilot  = @{ File = '.github/copilot-instructions.md'; Name = 'GitHub Copilot' }
            cursor   = @{ File = '.cursor/rules/specify-rules.mdc'; Name = 'Cursor IDE' }
            qwen     = @{ File = 'QWEN.md'; Name = 'Qwen Code' }
            opencode = @{ File = 'AGENTS.md'; Name = 'opencode' }
            codex    = @{ File = 'AGENTS.md'; Name = 'Codex CLI' }
            windsurf = @{ File = '.windsurf/rules/specify-rules.md'; Name = 'Windsurf' }
        }

        # Limits
        MAX_FILE_SIZE        = 1MB
    }
}
