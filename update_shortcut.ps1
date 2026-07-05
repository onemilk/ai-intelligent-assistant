$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "AI桌宠助手.lnk"
$TargetPath = Join-Path $PSScriptRoot "启动桌宠.vbs"

$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($ShortcutPath)
$s.TargetPath = $TargetPath
$s.WorkingDirectory = $PSScriptRoot
$s.Save()

Write-Host "done"
