Set WshShell = CreateObject("WScript.Shell")
' Этот код берет путь к папке, где лежит сам VBS файл
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
' И запускает start_bot.bat в этой же папке
WshShell.Run chr(34) & strPath & "\start_bot.bat" & chr(34), 0, False