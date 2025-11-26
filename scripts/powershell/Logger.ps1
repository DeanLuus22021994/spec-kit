class SpecKitLogger {
    [string]$Context

    SpecKitLogger([string]$context) {
        $this.Context = $context
    }

    hidden [void] Log([string]$message, [string]$level, [ConsoleColor]$color) {
        $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        $formattedMessage = "[$timestamp] [$level] [$($this.Context)] $message"
        Write-Host $formattedMessage -ForegroundColor $color
    }

    [void] Info([string]$message) {
        $this.Log($message, "INFO", [ConsoleColor]::Cyan)
    }

    [void] Warning([string]$message) {
        $this.Log($message, "WARN", [ConsoleColor]::Yellow)
    }

    [void] Error([string]$message) {
        $this.Log($message, "ERROR", [ConsoleColor]::Red)
    }

    [void] Success([string]$message) {
        $this.Log($message, "SUCCESS", [ConsoleColor]::Green)
    }
}
