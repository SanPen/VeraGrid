param(
    [string]$RuntimeRoot = "C:\Users\andre\.VeraGrid\external_python_packages\klu_cvxoptklu",
    [string]$BenchmarkRoot = "C:\Users\andre\PycharmProjects\VeraGrid\trunk\dynamics_emt\benchmark_results"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Add-Content -Path $Global:LogPath -Value $line
    Write-Host $line
}

function Write-StatusFile {
    param(
        [bool]$Success,
        [string]$Message,
        [string]$InstallPath = ""
    )

    $payload = @{
        success = $Success
        message = $Message
        install_path = $InstallPath
    }
    $payload | ConvertTo-Json | Set-Content -Path $Global:StatusPath -Encoding UTF8
}

New-Item -ItemType Directory -Force -Path $BenchmarkRoot | Out-Null
$Global:LogPath = Join-Path $BenchmarkRoot "klu_install_log.txt"
$Global:StatusPath = Join-Path $BenchmarkRoot "klu_install_status.json"
Set-Content -Path $Global:LogPath -Value ""
Write-StatusFile -Success $false -Message "started"

try {
    Write-Log "Starting elevated KLU toolchain/runtime installation"

    $vswherePath = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"

    if (Test-Path $vswherePath) {
        Write-Log "Using vswhere at $vswherePath"
    } else {
        throw "vswhere.exe was not found at the expected path"
    }

    $requiresComponent = "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"
    $existingInstall = & $vswherePath -latest -products * -requires $requiresComponent -property installationPath

    if ([string]::IsNullOrWhiteSpace($existingInstall)) {
        Write-Log "No VC++ Build Tools installation with $requiresComponent found. Installing via bootstrapper."

        $bootstrapperPath = Join-Path $BenchmarkRoot "vs_BuildTools_klu.exe"

        if (Test-Path $bootstrapperPath) {
            Write-Log "Reusing bootstrapper at $bootstrapperPath"
        } else {
            Write-Log "Downloading Build Tools bootstrapper"
            Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vs_BuildTools.exe" -OutFile $bootstrapperPath
        }

        Write-Log "Running Build Tools bootstrapper"
        Start-Process -FilePath $bootstrapperPath -ArgumentList "--quiet --wait --norestart --nocache --includeRecommended --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows11SDK.22621" -Wait
    } else {
        Write-Log "Existing VC++ Build Tools installation found at $existingInstall"
    }

    $installPath = & $vswherePath -latest -products * -requires $requiresComponent -property installationPath

    if ([string]::IsNullOrWhiteSpace($installPath)) {
        throw "VC++ Build Tools were not detected after installation"
    }

    Write-Log "Resolved Build Tools installation path: $installPath"

    $vsDevCmd = Join-Path $installPath "Common7\Tools\VsDevCmd.bat"

    if (Test-Path $vsDevCmd) {
        Write-Log "Using VsDevCmd at $vsDevCmd"
    } else {
        throw "VsDevCmd.bat was not found under the detected installation path"
    }

    New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
    Write-Log "Installing external runtime packages into $RuntimeRoot"

    $pythonExe = (Get-Command python).Source

    if ([string]::IsNullOrWhiteSpace($pythonExe)) {
        throw "Python executable not found in PATH"
    }

    $cmd = "call `"$vsDevCmd`" -host_arch=amd64 -arch=amd64 && `"$pythonExe`" -m pip install --upgrade --target `"$RuntimeRoot`" cvxopt cvxoptklu"
    Write-Log "Running developer prompt pip install"
    cmd.exe /c $cmd

    Write-Log "Finished elevated KLU toolchain/runtime installation"
    Write-StatusFile -Success $true -Message "completed" -InstallPath $installPath
}
catch {
    Write-Log ("FAILED: " + $_.Exception.Message)
    Write-StatusFile -Success $false -Message $_.Exception.Message
    throw
}
