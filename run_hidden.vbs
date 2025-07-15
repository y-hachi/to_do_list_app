Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run Chr(34) & "page_open.bat" & Chr(34), 0
Set WshShell = Nothing
Set fso = Nothing