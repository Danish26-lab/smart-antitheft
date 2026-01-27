' Run Agent Silently in Background (No Window)
' Double-click this file to start the agent without showing a window

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(scriptPath)

' Change to agent directory
WshShell.CurrentDirectory = scriptPath

' Run Python agent in hidden window
WshShell.Run "python agent.py", 0, False

' Optional: Show a brief message that agent started
WshShell.Popup "Agent started in background!", 2, "Anti-Theft Agent", 64
