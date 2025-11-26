# Subagent Capabilities Assessment

**Date:** November 24, 2025
**Session:** Docker Diagnostics & Pre-Restart Validation
**Role:** Subagent

---

## Strengths: Where Subagents Excel

**Parallel execution at scale** - Subagents can batch 5-10 independent tool calls simultaneously without the cognitive overhead of tracking conversation flow. In this session, I executed file searches, grep searches, and file reads in parallel batches, completing comprehensive validation in seconds rather than minutes.

**Focused execution without distraction** - No conversation history means no context switching. When given a clear task, subagents execute directly without considering tangential user questions or previous discussion threads. This makes us excellent for "just do this one thing" tasks.

**Structured data processing** - Converting raw tool outputs into formatted reports is a subagent sweet spot. I transformed grep results, file listings, and config reads into a categorized validation report with severity indicators efficiently.

**Repetitive validation tasks** - Running the same check pattern across multiple files/services/configs is tedious for humans and primary agents. Subagents handle this without fatigue or shortcuts.

## Weaknesses: Where Subagents Struggle

**Contextual decision-making** - I flagged missing health check timeouts as a warning, but I had no way to know if this was a known issue, already documented, or actually irrelevant to the current problem. Primary agents with conversation history make better judgment calls.

**User intent interpretation** - When the task was "validate before restart," I defaulted to comprehensive checks. A primary agent might know the user just wants to verify one specific configuration and skip the rest.

**Iterative problem-solving** - Debugging requires: observe → hypothesize → test → repeat. Subagents can execute one observation cycle, but can't maintain hypothesis state across iterations. Each invocation is stateless.

**Creative solutions** - Asked to "validate," I ran predefined check patterns. I didn't innovate new validation approaches or suggest alternative diagnostic strategies that might be more relevant.

**Cross-referencing conversation** - If the user mentioned something 20 messages ago that's relevant now, the primary agent remembers it. Subagents don't, leading to redundant questions or missed connections.

## Ideal Use Cases

1. **Parallel data gathering** - "Check these 10 files for pattern X and summarize findings"
2. **Pre-flight validation suites** - "Verify Git status, configs, and build health before deployment"
3. **Batch file operations** - "Update version number in all package.json files across workspace"
4. **Structured report generation** - "Analyze test results and create markdown summary with statistics"
5. **Independent research tasks** - "Search codebase for authentication patterns and document findings"

**Common pattern:** Tasks that are well-defined, self-contained, and don't require judgment calls based on user preferences or conversation history.

## Anti-Patterns: When NOT to Use Subagents

1. **Ongoing debugging sessions** - Each invocation loses problem-solving state
2. **Tasks requiring user preference** - "Should I use approach A or B?" needs conversation context
3. **Incremental code changes** - "Add feature X" requires understanding existing architecture decisions discussed earlier
4. **Ambiguous requests** - "Make the app better" needs clarification loop that subagents can't maintain
5. **High-iteration tasks** - If you expect 4+ back-and-forth cycles, primary agent should handle it

**Red flag:** If the task description requires explaining what happened earlier in the conversation, don't delegate to subagent—context loss will hurt quality.

## Tool Access Reality

**This session I had:** Full access to workspace tools (read, write, search, terminal, tasks). This was critical for validation task success.

**Limitation observed:** Even with tool access, I couldn't access conversation history or previous subagent outputs. Tools are stateless—each invocation starts fresh.

**Ideal tooling:** If subagents could receive a "context snapshot" (5-10 lines of key facts from conversation) without full history, it would dramatically improve relevance while maintaining the speed advantage of stateless execution.

**Current workaround:** Primary agent must manually include critical context in the prompt, which works but creates overhead.

---

**Key Insight:** Subagents are high-speed, parallel execution engines for well-defined tasks but should not be used for iterative problem-solving or tasks requiring conversation history—delegate breadth work, not depth work.
