param(
    [switch]$SkipRebuild
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if (-not $SkipRebuild) {
    Write-Host "Building Gambit C++ engine..." -ForegroundColor Cyan
    g++ -std=c++17 -O2 main.cpp Board.cpp Move.cpp Pawn.cpp Knight.cpp Bishop.cpp Rook.cpp Queen.cpp King.cpp Evaluation.cpp Search.cpp -o gambit.exe
    if ($LASTEXITCODE -ne 0) {
        throw "C++ build failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Generating application icon..." -ForegroundColor Cyan
python -c "from chess_utils import generate_app_icon; print(generate_app_icon())"
if ($LASTEXITCODE -ne 0) {
    throw "Icon generation failed."
}

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Gambit Chess.lnk"
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $RepoRoot "Launch Gambit Chess.vbs"
$Shortcut.WorkingDirectory = $RepoRoot
$Shortcut.IconLocation = Join-Path $RepoRoot "assets\gambit.ico"
$Shortcut.Description = "Launch Gambit Chess Desktop Application"
$Shortcut.Save()

Write-Host "Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
