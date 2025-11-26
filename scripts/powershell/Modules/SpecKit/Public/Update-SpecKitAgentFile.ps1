function Update-SpecKitAgentFile {
    param(
        [string]$TargetFile,
        [string]$AgentName,
        [object]$PlanData,
        [string]$CurrentBranch,
        [string]$RepoRoot,
        [object]$Config,
        [object]$Logger
    )

    $MaxFileSize = $Config.MAX_FILE_SIZE
    $RegexTimeout = [TimeSpan]::FromSeconds(2)

    function Initialize-AgentFile {
        param($targetFile, $agentName)
        try {
            if (Test-Path $targetFile) { return }

            $template = Join-Path $RepoRoot $Config.TEMPLATES_DIR_NAME $Config.AGENT_TEMPLATE_NAME
            if (-not (Test-Path $template)) {
                if ($Logger) { $Logger.Warning("Template not found: $template") }
                return
            }

            $content = Get-Content $template -Raw -ErrorAction Stop

            # Safe replacements
            $content = $content.Replace('[PROJECT NAME]', (Split-Path $RepoRoot -Leaf))
            $content = $content.Replace('[DATE]', (Get-Date -Format 'yyyy-MM-dd'))
            $content = $content.Replace('[EXTRACTED FROM ALL PLAN.MD FILES]', "- $($PlanData.Language) + $($PlanData.Framework) ($CurrentBranch)")

            if ($PlanData.ProjectType -match 'web') { $structure = "backend/`nfrontend/`ntests/" } else { $structure = "src/`ntests/" }
            $content = $content.Replace('[ACTUAL STRUCTURE FROM PLANS]', $structure)

            if ($PlanData.Language -match 'Python') { $commands = 'cd src && pytest && ruff check .' }
            elseif ($PlanData.Language -match 'Rust') { $commands = 'cargo test && cargo clippy' }
            elseif ($PlanData.Language -match 'JavaScript|TypeScript') { $commands = 'npm test && npm run lint' }
            else { $commands = "# Add commands for $($PlanData.Language)" }

            $content = $content.Replace('[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]', $commands)
            $content = $content.Replace('[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]', "$($PlanData.Language): Follow standard conventions")
            $content = $content.Replace('[LAST 3 FEATURES AND WHAT THEY ADDED]', "- ${CurrentBranch}: Added $($PlanData.Language) + $($PlanData.Framework)")

            # Ensure directory exists
            $parentDir = Split-Path $targetFile
            if (-not (Test-Path $parentDir)) {
                New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
            }

            $content | Set-Content $targetFile -Encoding UTF8 -ErrorAction Stop
            if ($Logger) { $Logger.Info("Initialized $agentName context file.") }
        }
        catch {
            if ($Logger) { $Logger.Error("Failed to initialize ${agentName}: $_") }
        }
    }

    try {
        if (-not (Test-Path $TargetFile)) {
            Initialize-AgentFile $TargetFile $AgentName
            return
        }

        # Check file size
        $fileItem = Get-Item $TargetFile
        if ($fileItem.Length -gt $MaxFileSize) {
            if ($Logger) { $Logger.Warning("File $TargetFile is too large ($($fileItem.Length) bytes). Skipping to prevent memory issues.") }
            return
        }

        $content = Get-Content $TargetFile -Raw -ErrorAction Stop

        # Safe Regex Update for Active Technologies
        if ($PlanData.Language -and ($content -notmatch [regex]::Escape($PlanData.Language))) {
            $content = $content -replace '(## Active Technologies\r?\n)', "`$1- $($PlanData.Language) + $($PlanData.Framework) ($CurrentBranch)`n"
        }
        if ($PlanData.Database -and $PlanData.Database -ne 'N/A' -and ($content -notmatch [regex]::Escape($PlanData.Database))) {
            $content = $content -replace '(## Active Technologies\r?\n)', "`$1- $($PlanData.Database) ($CurrentBranch)`n"
        }

        # Safe Regex Update for Recent Changes with Timeout
        try {
            $pattern = '## Recent Changes\r?\n([\s\S]*?)(\r?\n\r?\n|$)'
            $regex = [regex]::new($pattern, [System.Text.RegularExpressions.RegexOptions]::None, $RegexTimeout)
            $match = $regex.Match($content)

            if ($match.Success) {
                $changesBlock = $match.Groups[1].Value.Trim().Split("`n")
                # Prepend new change
                $newChange = "- ${CurrentBranch}: Added $($PlanData.Language) + $($PlanData.Framework)"
                $changesBlock = ,$newChange + $changesBlock
                # Keep only top 3 unique non-empty lines
                $changesBlock = $changesBlock | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique | Select-Object -First 3
                $joined = ($changesBlock -join "`n")

                # Replace safely
                $content = $regex.Replace($content, "## Recent Changes`n$joined`n`n", 1)
            }
        }
        catch [System.Text.RegularExpressions.RegexMatchTimeoutException] {
            if ($Logger) { $Logger.Warning("Regex timed out while processing Recent Changes in $TargetFile. Skipping this section.") }
        }

        # Update Date
        $content = [regex]::Replace($content, 'Last updated: \d{4}-\d{2}-\d{2}', "Last updated: $(Get-Date -Format 'yyyy-MM-dd')")

        $content | Set-Content $TargetFile -Encoding UTF8 -ErrorAction Stop
        if ($Logger) { $Logger.Success("✓ $AgentName context file updated successfully") }
    }
    catch {
        if ($Logger) { $Logger.Error("Failed to update ${AgentName}: $_") }
    }
}
