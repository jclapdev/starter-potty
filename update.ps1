<#
update.ps1 - one-line updater for the Claudian vault system (Windows).

The companion to install.ps1. install.ps1 is run once on a bare machine; this is
run whenever you want the latest system improvements. It never touches your
notes, projects, history, memory, main.md, or machine settings - only the system
files are refreshed.

One-liner (paste into PowerShell):
  irm https://raw.githubusercontent.com/jclapdev/starter-potty/main/update.ps1 | iex

It finds your vault, makes sure the updater is present (fetching it the first
time if needed), and runs it. Safe to re-run.

Override the vault location with:  $env:CLAUDIAN_VAULT_DIR = "C:\path"; then run.
Pass through to the updater, e.g. offline:  .\update.ps1 --from new-version.zip
#>
[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)] $PassThrough)

$ErrorActionPreference = "Stop"
$RawBase = "https://raw.githubusercontent.com/jclapdev/starter-potty/main"

function Say($m) { Write-Host "  $m" }
function Die($m) { Write-Error $m; exit 1 }

# 1. Locate the vault.
$VaultDir = if ($env:CLAUDIAN_VAULT_DIR) { $env:CLAUDIAN_VAULT_DIR } else { Join-Path $HOME "ClaudeVault" }
if (-not (Test-Path (Join-Path $VaultDir "AI-Workshop"))) {
  if (Test-Path (Join-Path $PWD "AI-Workshop")) {
    $VaultDir = "$PWD"
  } else {
    Die "No vault found at $VaultDir (no AI-Workshop folder).`n       Set CLAUDIAN_VAULT_DIR to your vault, or run this from inside it.`n       Starting fresh on a bare machine? Use install.ps1 instead."
  }
}
Say "Vault: $VaultDir"

# 2. Pick a Python.
$Py = $null
foreach ($c in @("python", "python3", "py")) {
  if (Get-Command $c -ErrorAction SilentlyContinue) { $Py = $c; break }
}
if (-not $Py) { Die "Python 3 is not installed. Install it, then re-run." }

# 3. Make sure the updater is present; fetch it the first time if not.
$Updater = Join-Path $VaultDir "AI-Workshop\update.py"
if (-not (Test-Path $Updater)) {
  Say "First run on this machine - fetching the updater..."
  New-Item -ItemType Directory -Force -Path (Split-Path $Updater) | Out-Null
  try { Invoke-WebRequest "$RawBase/AI-Workshop/update.py" -OutFile $Updater }
  catch { Die "Could not download the updater (no internet?)." }
}

# 4. Run it from the vault folder, passing through any extra flags.
Say "Updating..."
Push-Location $VaultDir
try { & $Py "AI-Workshop\update.py" @PassThrough }
finally { Pop-Location }
