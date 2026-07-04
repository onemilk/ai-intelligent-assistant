$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "AI桌宠助手.lnk"
$TargetPath = Join-Path $PSScriptRoot "启动桌宠.bat"

$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($ShortcutPath)
$s.TargetPath = $TargetPath
$s.WorkingDirectory = $PSScriptRoot
$s.Save()

Write-Host "桌面快捷方式已创建: $ShortcutPath"
