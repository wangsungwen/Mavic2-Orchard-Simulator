@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 -winsdk=10.0.19041.0
if errorlevel 1 exit /b 1
set "PATH=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin;%PATH%"
cd /d "%~dp0..\vendor\AirSim"
call build.cmd --no-full-poly-car
if errorlevel 1 exit /b 1
if not exist "Unreal\Environments\Blocks\Blocks.sln" (
    echo AirSim libraries built, but Blocks.sln is missing. Install and register UE 4.27.2, then generate project files. 1>&2
    exit /b 2
)
exit /b 0

