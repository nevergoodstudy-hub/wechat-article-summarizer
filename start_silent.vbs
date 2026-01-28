' 微信文章总结器 - 静默启动脚本
' 此脚本启动 GUI 程序，不显示任何控制台窗口

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' 使用虚拟环境中的 pythonw.exe (无控制台窗口)
pythonwPath = scriptPath & "\.venv\Scripts\pythonw.exe"

' 启动器脚本路径
launcherPath = scriptPath & "\run_gui.pyw"

' 检查虚拟环境是否存在
If Not fso.FileExists(pythonwPath) Then
    MsgBox "虚拟环境未找到: " & pythonwPath & vbCrLf & vbCrLf & "请先运行: python -m venv .venv", vbCritical, "错误"
    WScript.Quit 1
End If

' 检查启动器是否存在
If fso.FileExists(launcherPath) Then
    ' 以隐藏方式运行
    WshShell.Run """" & pythonwPath & """ """ & launcherPath & """", 0, False
Else
    MsgBox "启动器脚本不存在: " & launcherPath, vbCritical, "错误"
End If

Set fso = Nothing
Set WshShell = Nothing
