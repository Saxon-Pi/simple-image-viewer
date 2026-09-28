$exePath = "C:\Apps\SimpleImageViewer\SimpleImageViewer.exe"

reg add "HKCU\Software\Classes\SimpleImageViewer.Image" /ve /d "Simple Image Viewer" /f
reg add "HKCU\Software\Classes\SimpleImageViewer.Image\shell\open\command" /ve /d "`"$exePath`" `"%1`"" /f

reg add "HKCU\Software\Classes\.webp" /ve /d "SimpleImageViewer.Image" /f
reg add "HKCU\Software\Classes\.png" /ve /d "SimpleImageViewer.Image" /f
reg add "HKCU\Software\Classes\.jpg" /ve /d "SimpleImageViewer.Image" /f
reg add "HKCU\Software\Classes\.jpeg" /ve /d "SimpleImageViewer.Image" /f
