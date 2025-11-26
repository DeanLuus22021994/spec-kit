function Invoke-SpecKitBlock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [ScriptBlock]$ScriptBlock,

        [Parameter(Mandatory = $false)]
        [System.Collections.IDictionary]$Variables
    )

    # Defensive Programming
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'

    # Initialize Logger
    $logger = [SpecKitLogger]::new($Name)

    try {
        # Execute the script block
        & $ScriptBlock $logger
    }
    catch {
        $logger.Error("Critical Error in $Name : $_")
        $logger.Error($_.ScriptStackTrace)
        exit 1
    }
}
