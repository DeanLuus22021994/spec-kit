function Get-SpecKitPlanData {
    param(
        [string]$PlanPath,
        [object]$Logger
    )

    if (-not (Test-Path $PlanPath)) {
        if ($Logger) { $Logger.Warning("No plan.md found at $PlanPath.") }
        return $null
    }

    function Get-PlanValue {
        param([string]$pattern)
        try {
            # Read line by line to avoid loading large files
            foreach ($line in Get-Content $PlanPath -ErrorAction Stop) {
                if ($line -match "^\*\*$pattern\*\*: (.*)") {
                    return $matches[1].Trim()
                }
            }
        }
        catch {
            if ($Logger) { $Logger.Warning("Error reading plan value for '$pattern': $_") }
        }
        return ''
    }

    $newLang = Get-PlanValue 'Language/Version'
    $newFramework = Get-PlanValue 'Primary Dependencies'
    $newDb = Get-PlanValue 'Storage'
    $newProjectType = Get-PlanValue 'Project Type'

    if ($Logger) {
        $Logger.Info("Parsing plan data from $PlanPath")
        if ($newLang) { $Logger.Info("Found language: $newLang") } else { $Logger.Warning("No language information found in plan") }
        if ($newFramework) { $Logger.Info("Found framework: $newFramework") }
        if ($newDb -and $newDb -ne 'N/A') { $Logger.Info("Found database: $newDb") }
        if ($newProjectType) { $Logger.Info("Found project type: $newProjectType") }
    }

    return [PSCustomObject]@{
        Language    = $newLang
        Framework   = $newFramework
        Database    = $newDb
        ProjectType = $newProjectType
    }
}
