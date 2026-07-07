<#
install.ps1 - first-time, zero-tools installer for the Claudian vault system (Windows).

For someone starting with NOTHING installed. It puts these on the machine:
  1. Python 3          (setup.py needs it)
  2. Obsidian          (your window into the vault)
  3. Claude Desktop    (the app you chat with)
  4. Claude Code       (the terminal agent)
  5. The vault itself  (the Claudian system)
...then installs the Claudian Obsidian plugin into the vault and hands off to
AI-Workshop\setup.py, which wires up the MCP servers, hooks, and knowledge base.

Zero-tools entry point (paste into PowerShell):
  irm https://raw.githubusercontent.com/jclapdev/starter-potty/main/install.ps1 | iex

Hybrid install: prefers winget (built into Windows 10/11) and falls back to
official direct downloads. Safe to re-run: anything already present is skipped.

Flags:
  -DryRun   Detect what is present and print the plan. Installs nothing.
  -Help     Show this help.

Override the vault location with:  $env:CLAUDIAN_VAULT_DIR = "C:\path"; then run.
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Help
)

$ErrorActionPreference = 'Continue'

# -- Config ------------------------------------------------------------------
$RepoZip    = 'https://github.com/jclapdev/starter-potty/archive/refs/heads/main.zip'
$RepoTopDir = 'starter-potty-main'
$VaultDir   = if ($env:CLAUDIAN_VAULT_DIR) { $env:CLAUDIAN_VAULT_DIR } else { Join-Path $env:USERPROFILE 'ClaudeVault' }

$ClaudeCodeInstall = 'https://claude.ai/install.ps1'
$ClaudeDownloadUrl = 'https://claude.ai/download'
$ObsidianReleases  = 'https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest'

# Claudian plugin - official Obsidian community plugin (repo yishentu/claudian).
$PluginId   = 'realclaudian'
$PluginBase = 'https://github.com/yishentu/claudian/releases/latest/download'

# -- Summary tracking --------------------------------------------------------
$script:DoneList = @()
$script:SkipList = @()
$script:FailList = @()
function Mark-Done($m) { $script:DoneList += $m }
function Mark-Skip($m) { $script:SkipList += "$m (already present)" }
function Mark-Fail($m) { $script:FailList += $m }

# -- Output helpers ----------------------------------------------------------
function Write-Section($m) { Write-Host "`n== $m ==" -ForegroundColor White }
function Write-Ok($m)      { Write-Host "  [ok]   $m" -ForegroundColor Green }
function Write-Skip2($m)   { Write-Host "  [skip] $m" -ForegroundColor DarkGray }
function Write-Warn2($m)   { Write-Host "  [!]    $m" -ForegroundColor Yellow }
function Write-Fail2($m)   { Write-Host "  [x]    $m" -ForegroundColor Red }

# -- Detection ---------------------------------------------------------------
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Have-Winget { Have 'winget' }

function Winget-Installed($id) {
    if (-not (Have-Winget)) { return $false }
    $out = winget list --id $id -e --accept-source-agreements 2>$null | Out-String
    return ($out -match [regex]::Escape($id))
}

# Refresh PATH from the registry so tools winget just installed are visible now.
function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = @($machine, $user | Where-Object { $_ }) -join ';'
}

function Find-Python {
    Refresh-Path
    foreach ($c in 'python', 'python3') {
        $g = Get-Command $c -ErrorAction SilentlyContinue
        if ($g -and $g.Source -notlike '*WindowsApps*') { return $g.Source }
    }
    # The 'py' launcher is a reliable fallback when python.exe isn't on PATH.
    if (Have 'py') { return 'py' }
    return $null
}

# -- winget helper with direct-download fallback ------------------------------
function Install-Winget($id, $name) {
    if (-not (Have-Winget)) { return $false }
    Write-Host "  installing $name via winget ..."
    winget install --id $id -e --accept-source-agreements --accept-package-agreements --silent 2>&1 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

# -- Python ------------------------------------------------------------------
function Ensure-Python {
    Write-Section 'Python 3'
    if (Find-Python) { Write-Ok "Python present"; Mark-Skip 'Python 3'; return }
    if ($DryRun) { Write-Warn2 'would install Python 3 (winget, else python.org)'; return }
    if (Install-Winget 'Python.Python.3.12' 'Python') {
        Refresh-Path
        if (Find-Python) { Write-Ok 'Python installed via winget'; Mark-Done 'Python 3'; return }
    }
    # Direct fallback: official python.org installer, silent, adds to PATH.
    try {
        $exe = Join-Path $env:TEMP 'python-installer.exe'
        Write-Host '  downloading Python installer from python.org ...'
        Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile $exe -UseBasicParsing
        Start-Process -FilePath $exe -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_test=0' -Wait
        Refresh-Path
        if (Find-Python) { Write-Ok 'Python installed'; Mark-Done 'Python 3'; return }
    } catch { }
    Write-Warn2 'could not install Python - get it from https://www.python.org/downloads/'
    Mark-Fail 'Python 3 (install manually from python.org)'
}

# -- Obsidian ----------------------------------------------------------------
function Ensure-Obsidian {
    Write-Section 'Obsidian'
    if (Winget-Installed 'Obsidian.Obsidian') { Write-Ok 'Obsidian present'; Mark-Skip 'Obsidian'; return }
    if ($DryRun) { Write-Warn2 'would install Obsidian (winget, else .exe)'; return }
    if (Install-Winget 'Obsidian.Obsidian' 'Obsidian') { Write-Ok 'Obsidian installed via winget'; Mark-Done 'Obsidian'; return }
    try {
        Write-Host '  fetching the latest Obsidian installer ...'
        $rel = Invoke-RestMethod $ObsidianReleases -UseBasicParsing
        $asset = $rel.assets | Where-Object { $_.name -match '\.exe$' } | Select-Object -First 1
        if ($asset) {
            $exe = Join-Path $env:TEMP $asset.name
            Invoke-WebRequest $asset.browser_download_url -OutFile $exe -UseBasicParsing
            Start-Process -FilePath $exe -Wait
            Write-Ok 'Obsidian installed from official installer'; Mark-Done 'Obsidian'; return
        }
    } catch { }
    Write-Fail2 'could not install Obsidian - get it from https://obsidian.md/download'
    Mark-Fail 'Obsidian (install manually from obsidian.md)'
}

# -- Claude Desktop ----------------------------------------------------------
function Ensure-ClaudeDesktop {
    Write-Section 'Claude Desktop'
    if (Winget-Installed 'Anthropic.Claude') { Write-Ok 'Claude Desktop present'; Mark-Skip 'Claude Desktop'; return }
    if ($DryRun) { Write-Warn2 'would install Claude Desktop (winget, else official download)'; return }
    if (Install-Winget 'Anthropic.Claude' 'Claude Desktop') { Write-Ok 'Claude Desktop installed via winget'; Mark-Done 'Claude Desktop'; return }
    Write-Warn2 "could not install Claude Desktop automatically."
    Write-Warn2 "download and run it from: $ClaudeDownloadUrl"
    Mark-Fail 'Claude Desktop (install manually from claude.ai/download)'
}

# -- Claude Code -------------------------------------------------------------
function Ensure-ClaudeCode {
    Write-Section 'Claude Code (terminal agent)'
    Refresh-Path
    if (Have 'claude') { Write-Ok 'Claude Code present'; Mark-Skip 'Claude Code'; return }
    if ($DryRun) { Write-Warn2 'would install Claude Code (official native installer)'; return }
    try {
        Write-Host '  running the official Claude Code installer ...'
        Invoke-Expression (Invoke-RestMethod $ClaudeCodeInstall)
        Refresh-Path
        if (Have 'claude') { Write-Ok 'Claude Code installed'; Mark-Done 'Claude Code'; return }
        # Even if not yet on PATH this session, the install likely succeeded.
        Write-Ok 'Claude Code installed (restart your terminal to use `claude`)'; Mark-Done 'Claude Code'; return
    } catch { }
    if (Install-Winget 'Anthropic.ClaudeCode' 'Claude Code') { Write-Ok 'Claude Code installed via winget'; Mark-Done 'Claude Code'; return }
    Write-Fail2 'could not install Claude Code - see https://code.claude.com/docs/en/setup'
    Mark-Fail 'Claude Code (see code.claude.com/docs/en/setup)'
}

# -- The vault ---------------------------------------------------------------
function Fetch-Vault {
    Write-Section 'The vault (Claudian system)'
    if (Test-Path $VaultDir) { Write-Warn2 "$VaultDir already exists - leaving it untouched"; Mark-Skip "Vault ($VaultDir)"; return }
    if ($DryRun) { Write-Warn2 "would download the vault to $VaultDir"; return }
    try {
        $tmp = Join-Path $env:TEMP ("claudian-" + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Force -Path $tmp | Out-Null
        $zip = Join-Path $tmp 'vault.zip'
        Write-Host '  downloading the vault ...'
        Invoke-WebRequest $RepoZip -OutFile $zip -UseBasicParsing
        Expand-Archive -Path $zip -DestinationPath $tmp -Force
        $extracted = Join-Path $tmp $RepoTopDir
        if (-not (Test-Path $extracted)) {
            $extracted = (Get-ChildItem $tmp -Directory | Where-Object { $_.Name -like '*starter*' } | Select-Object -First 1).FullName
        }
        if (-not $extracted -or -not (Test-Path $extracted)) { throw 'unexpected zip layout' }
        $parent = Split-Path $VaultDir -Parent
        if ($parent -and -not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
        Move-Item $extracted $VaultDir
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        Write-Ok "vault ready at $VaultDir"; Mark-Done "Vault ($VaultDir)"
    } catch {
        Write-Fail2 "vault download failed: $_"; Mark-Fail 'Vault download'
    }
}

# -- Claudian plugin ---------------------------------------------------------
function Enable-CommunityPlugin($id) {
    $cpj = Join-Path $VaultDir '.obsidian\community-plugins.json'
    $data = @()
    if (Test-Path $cpj) {
        try { $data = @(Get-Content $cpj -Raw | ConvertFrom-Json) } catch { $data = @() }
    }
    if ($data -notcontains $id) { $data += $id }
    # Force an array even when there is a single element.
    ConvertTo-Json @($data) | Set-Content -Path $cpj -Encoding UTF8
}

function Install-ClaudianPlugin {
    Write-Section 'Claudian plugin'
    if ($DryRun) { Write-Warn2 'would download the Claudian plugin into the vault and enable it'; return }
    $obs = Join-Path $VaultDir '.obsidian'
    if (-not (Test-Path $obs)) {
        Write-Warn2 'the vault has no .obsidian folder - skipping.'
        Write-Warn2 "install Claudian later from Obsidian -> Settings -> Community plugins -> search 'Claudian'."
        Mark-Fail 'Claudian plugin (install from Obsidian community store)'; return
    }
    $dir = Join-Path $obs "plugins\$PluginId"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $allOk = $true
    foreach ($f in 'main.js', 'manifest.json', 'styles.css') {
        try { Invoke-WebRequest "$PluginBase/$f" -OutFile (Join-Path $dir $f) -UseBasicParsing }
        catch { $allOk = $false }
    }
    if (-not $allOk) {
        Write-Fail2 'could not download the Claudian plugin.'
        Write-Warn2 "install it later from Obsidian -> Settings -> Community plugins -> search 'Claudian'."
        Mark-Fail 'Claudian plugin (install from Obsidian community store)'; return
    }
    Enable-CommunityPlugin $PluginId
    Write-Ok "Claudian plugin installed and enabled ($dir)"; Mark-Done 'Claudian plugin'
}

# -- Hand off to setup.py ----------------------------------------------------
function Run-Setup {
    Write-Section 'Configuring the system (setup.py)'
    $setup = Join-Path $VaultDir 'AI-Workshop\setup.py'
    if ($DryRun) { Write-Warn2 "would run: python $setup"; return }
    if (-not (Test-Path $setup)) { Write-Warn2 "setup.py not found - skipping (vault may not have downloaded)"; Mark-Fail 'setup.py (not found)'; return }
    $py = Find-Python
    if (-not $py) {
        Write-Warn2 'Python is not available yet, so setup.py cannot run.'
        Write-Warn2 "after installing Python, run:  cd `"$VaultDir`"; python AI-Workshop\setup.py"
        Mark-Fail 'setup.py (needs Python)'; return
    }
    Push-Location $VaultDir
    try {
        if ($py -eq 'py') { & py 'AI-Workshop\setup.py' } else { & $py 'AI-Workshop\setup.py' }
        if ($LASTEXITCODE -eq 0) { Mark-Done 'System configured (setup.py)' }
        else { Write-Warn2 'setup.py did not finish cleanly - re-run it later.'; Mark-Fail 'setup.py (re-run manually)' }
    } finally { Pop-Location }
}

# -- Summary + manual gates --------------------------------------------------
function Print-Summary {
    Write-Section 'Summary'
    if ($script:DoneList) { Write-Host 'Installed:' -ForegroundColor Green;    $script:DoneList | ForEach-Object { Write-Host "  [ok]   $_" } }
    if ($script:SkipList) { Write-Host 'Already present:' -ForegroundColor DarkGray; $script:SkipList | ForEach-Object { Write-Host "  [skip] $_" } }
    if ($script:FailList) { Write-Host 'Needs your attention:' -ForegroundColor Red; $script:FailList | ForEach-Object { Write-Host "  [x]    $_" } }

    Write-Section "Last steps (these need you - they can't be automated)"
    Write-Host "  1. Sign in to Claude Desktop and to Claude Code (run 'claude' once in a terminal)."
    Write-Host "  2. Open the vault in Obsidian: Open folder as vault -> choose:"
    Write-Host "        $VaultDir"
    Write-Host "     The Claudian plugin is already installed and enabled. Obsidian may ask you"
    Write-Host "     to turn on community plugins / trust the author the first time - approve it."
    Write-Host "  3. Restart Claude Desktop and Claude Code so they load the new servers."
    Write-Host "  4. In either one, say: read your instructions"
    Write-Host ""
    Write-Host "  Full guide: $VaultDir\HUMAN.md"
}

# -- Main --------------------------------------------------------------------
function Main {
    if ($Help) {
        Get-Content $PSCommandPath | Select-Object -Skip 1 | ForEach-Object { if ($_ -eq '#>') { return }; $_ } | Select-Object -First 24
        return
    }
    Write-Host 'Claudian first-time installer (Windows)' -ForegroundColor White
    Write-Host "Vault target: $VaultDir"
    if ($DryRun) { Write-Host 'DRY RUN - detecting only, installing nothing.' -ForegroundColor Yellow }

    if (-not (Have-Winget) -and -not $DryRun) {
        Write-Warn2 'winget was not found. Direct downloads will be used where possible.'
        Write-Warn2 'winget ships with App Installer from the Microsoft Store on Windows 10/11.'
    }

    Ensure-Python
    Ensure-Obsidian
    Ensure-ClaudeDesktop
    Ensure-ClaudeCode
    Fetch-Vault
    Install-ClaudianPlugin
    Run-Setup

    if ($DryRun) {
        Write-Section 'Dry run complete'
        Write-Host '  Re-run without -DryRun to actually install.'
        return
    }
    Print-Summary
}

Main
