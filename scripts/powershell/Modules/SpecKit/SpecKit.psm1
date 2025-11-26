# Load Classes
. "$PSScriptRoot/Classes/Logger.ps1"

# Load Public Functions
Get-ChildItem -Path "$PSScriptRoot/Public/*.ps1" | ForEach-Object {
    . $_.FullName
}

# Export Functions
Export-ModuleMember -Function *
