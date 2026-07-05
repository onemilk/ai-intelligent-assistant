Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\python\project\PythonProject\luodi_able"
WshShell.Run "uv run python launch_desk_pet.py", 0, False
