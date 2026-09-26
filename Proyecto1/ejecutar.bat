@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys, tkinter; sys.exit(sys.version_info < (3,10))" >nul 2>nul
if not errorlevel 1 goto usar_py
python -c "import sys, tkinter; sys.exit(sys.version_info < (3,10))" >nul 2>nul
if not errorlevel 1 goto usar_python
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" goto usar_runtime_local
echo Instale Python 3.10 o superior con Tcl/Tk desde python.org.
pause
exit /b 2
:usar_py
py -3 main.py
goto fin
:usar_python
python main.py
goto fin
:usar_runtime_local
"%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" main.py
:fin
if errorlevel 1 pause
