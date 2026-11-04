@echo off
rem ============================================================
rem  把 .dat 拖到这个文件上，自动转换成多种词库格式
rem  输出在 .dat 同目录的 out\ 文件夹里
rem  需要先装 Python 3.9+（安装时勾选 Add to PATH）
rem ============================================================
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo 用法：把微软拼音导出的 ChsPinyinUDL.dat 拖到 这个 .bat 上。
    echo.
    pause
    exit /b 0
)

where python >nul 2>nul
if errorlevel 1 (
    echo 找不到 python，请先安装 Python 3.9 或更新版本，并在安装时勾选 "Add python.exe to PATH"。
    pause
    exit /b 1
)

set "OUTDIR=%~dp1out"

python "%~dp0run.py" %* -f all -o "%OUTDIR%"
if errorlevel 1 (
    echo.
    echo 转换失败，请把上面的报错信息发到项目的 Issues。
    pause
    exit /b 1
)

echo.
echo 转换完成，输出目录：%OUTDIR%
pause
