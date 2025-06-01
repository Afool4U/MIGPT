@echo off
chcp 65001 > nul
title MIGPT-易 智能助手控制面板

:menu
cls
echo ============================================
echo           MIGPT-易 智能助手控制面板
echo ============================================
echo.
echo  MIGPT-易 - 让您的小爱同学秒变AI助手
echo  支持多设备、多模型、HomeAssistant集成
echo.
echo ============================================
echo.
call echo  1) Start MIGPT     (启动程序)
call echo  2) Settings        (配置设置)
call echo  3) Install         (安装依赖)
call echo  4) Create Basic    (便携版)
call echo  5) Full Package    (完整版)
call echo  6) Exit            (退出程序)
echo.
echo ============================================
echo  首次使用请先选择3安装依赖，再选择2进行配置

set /p choice=请选择操作 (1-6): 

if "%choice%"=="1" goto start_program
if "%choice%"=="2" goto open_config
if "%choice%"=="3" goto install_deps
if "%choice%"=="4" goto create_portable
if "%choice%"=="5" goto create_bundled_portable
if "%choice%"=="6" goto exit_program

echo 输入有误，请重新选择!
timeout /t 2 > nul
goto menu

:start_program
cls
echo ============================================
echo             正在启动MIGPT-易...
echo ============================================
echo.
echo 注意: 如果在配置中启用了API服务器自动启动，
echo       API服务器将会自动启动
echo.
echo 常用命令:
echo  - help     : 显示帮助信息
echo  - status   : 显示当前状态
echo  - select   : 重新选择设备
echo  - on/off   : 开启/关闭AI回答模式
echo.
python -m MIGPT
goto menu

:open_config
cls
echo ============================================
echo           正在打开MIGPT-易配置界面
echo ============================================
echo.
echo 配置界面包含以下选项卡:
echo  - 基本设置: 小米账号和设备设置
echo  - API设置: 大模型API配置
echo  - HomeAssistant: 智能家居集成
echo  - 高级设置: JSON配置直接编辑
echo.
python config_gui.py
goto menu

:install_deps
cls
echo =============================================
echo        MIGPT-易 安装和设置向导
echo =============================================
echo.

:: 检查Python环境
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 您可以从 https://www.python.org/downloads/ 下载Python
    pause
    goto menu
)

:: 显示Python版本
echo [信息] 检测到Python版本:
python --version
echo.

:: 清理缓存
echo [信息] 正在清理缓存文件...
if exist __pycache__ rmdir /s /q __pycache__

:: 安装依赖
echo [信息] 正在安装依赖项...
pip install -r requirements.txt

echo.
echo [成功] 安装完成！按任意键返回主菜单...
pause > nul
goto menu

:create_portable
cls
echo =============================================
echo        MIGPT-易 便携版打包工具
echo =============================================
echo.
echo 此工具将创建一个便携版本的MIGPT-易，可复制到其他电脑使用
echo 便携版需要目标电脑已安装Python环境
echo.

:: 创建目标目录
if not exist "portable_MIGPT\" mkdir "portable_MIGPT"

echo [信息] 正在清理旧版本...
:: 清理目录但保留配置
if exist "portable_MIGPT\config.json" (
    copy "portable_MIGPT\config.json" "temp_config.json" >nul
    rmdir /s /q "portable_MIGPT"
    mkdir "portable_MIGPT"
    copy "temp_config.json" "portable_MIGPT\config.json" >nul
    del "temp_config.json"
) else (
    rmdir /s /q "portable_MIGPT"
    mkdir "portable_MIGPT"
)

echo [信息] 正在复制必要文件...

:: 复制文件
copy "*.py" "portable_MIGPT\" >nul
copy "migpt.bat" "portable_MIGPT\" >nul
copy "requirements.txt" "portable_MIGPT\" >nul
copy "LICENSE" "portable_MIGPT\" >nul
copy "README.md" "portable_MIGPT\" >nul
copy "README_QIANFAN.md" "portable_MIGPT\" >nul
copy ".gitignore" "portable_MIGPT\" >nul

if exist "config.json" (
    echo 是否包含当前配置文件？(Y/N)
    set /p include_config=
    if /i "%include_config%"=="Y" (
        copy "config.json" "portable_MIGPT\" >nul
        echo [信息] 已包含配置文件
    ) else (
        echo [信息] 已排除配置文件
    )
) else (
    echo [警告] 未找到配置文件，首次启动时需要配置
)

:: 创建启动脚本
echo @echo off > "portable_MIGPT\启动MIGPT.bat"
echo chcp 65001 ^> nul >> "portable_MIGPT\启动MIGPT.bat"
echo title MIGPT-易 便携版 >> "portable_MIGPT\启动MIGPT.bat"
echo. >> "portable_MIGPT\启动MIGPT.bat"
echo echo 正在检查环境... >> "portable_MIGPT\启动MIGPT.bat"
echo. >> "portable_MIGPT\启动MIGPT.bat"
echo :: 检查Python >> "portable_MIGPT\启动MIGPT.bat"
echo where python ^>nul 2^>nul >> "portable_MIGPT\启动MIGPT.bat"
echo if %%ERRORLEVEL%% neq 0 ( >> "portable_MIGPT\启动MIGPT.bat"
echo     echo 未检测到Python，请先安装Python 3.8或更高版本 >> "portable_MIGPT\启动MIGPT.bat"
echo     echo 您可以从 https://www.python.org/downloads/ 下载Python >> "portable_MIGPT\启动MIGPT.bat"
echo     pause >> "portable_MIGPT\启动MIGPT.bat"
echo     exit /b 1 >> "portable_MIGPT\启动MIGPT.bat"
echo ) >> "portable_MIGPT\启动MIGPT.bat"
echo. >> "portable_MIGPT\启动MIGPT.bat"
echo :: 检查配置文件 >> "portable_MIGPT\启动MIGPT.bat"
echo if not exist config.json ( >> "portable_MIGPT\启动MIGPT.bat"
echo     echo 未找到配置文件，将为您打开配置界面 >> "portable_MIGPT\启动MIGPT.bat"
echo     python config_gui.py >> "portable_MIGPT\启动MIGPT.bat"
echo ) >> "portable_MIGPT\启动MIGPT.bat"
echo. >> "portable_MIGPT\启动MIGPT.bat"
echo :: 清理缓存 >> "portable_MIGPT\启动MIGPT.bat"
echo if exist __pycache__ rmdir /s /q __pycache__ >> "portable_MIGPT\启动MIGPT.bat"
echo. >> "portable_MIGPT\启动MIGPT.bat"
echo echo 正在启动MIGPT-易便携版... >> "portable_MIGPT\启动MIGPT.bat"
echo python -m MIGPT >> "portable_MIGPT\启动MIGPT.bat"
echo. >> "portable_MIGPT\启动MIGPT.bat"
echo pause >> "portable_MIGPT\启动MIGPT.bat"

echo.
echo =============================================
echo         便携版打包完成！
echo =============================================
echo.
echo MIGPT-易便携版已创建在portable_MIGPT文件夹中。
echo 您可以将此文件夹复制到其他电脑使用。
echo.
pause
goto menu

:create_bundled_portable
cls
echo =============================================
echo      MIGPT-易 完整版打包工具(含依赖)
echo =============================================
echo.
echo 此工具将创建包含所有依赖的完整版本
echo 用户无需联网即可在其他电脑上安装使用
echo.
echo 注意: 此过程将下载所有依赖包(约100-200MB)
echo.
echo 是否继续？(Y/N)
set /p continue_bundle=
if /i not "%continue_bundle%"=="Y" goto menu

:: 创建目标目录
if not exist "portable_MIGPT_Full\" mkdir "portable_MIGPT_Full"

echo [信息] 正在清理旧版本...
:: 清理目录但保留配置
if exist "portable_MIGPT_Full\config.json" (
    copy "portable_MIGPT_Full\config.json" "temp_config.json" >nul
    rmdir /s /q "portable_MIGPT_Full"
    mkdir "portable_MIGPT_Full"
    copy "temp_config.json" "portable_MIGPT_Full\config.json" >nul
    del "temp_config.json"
) else (
    rmdir /s /q "portable_MIGPT_Full"
    mkdir "portable_MIGPT_Full"
)

echo [信息] 正在复制必要文件...

:: 复制文件
copy "*.py" "portable_MIGPT_Full\" >nul
copy "migpt.bat" "portable_MIGPT_Full\" >nul
copy "requirements.txt" "portable_MIGPT_Full\" >nul
copy "LICENSE" "portable_MIGPT_Full\" >nul
copy "README.md" "portable_MIGPT_Full\" >nul
copy "README_QIANFAN.md" "portable_MIGPT_Full\" >nul
copy ".gitignore" "portable_MIGPT_Full\" >nul

if exist "config.json" (
    echo 是否包含当前配置文件？(Y/N)
    set /p include_config=
    if /i "%include_config%"=="Y" (
        copy "config.json" "portable_MIGPT_Full\" >nul
        echo [信息] 已包含配置文件
    ) else (
        echo [信息] 已排除配置文件
    )
) else (
    echo [警告] 未找到配置文件，首次启动时需要配置
)

:: 创建依赖文件夹
echo [信息] 正在创建requires文件夹...
if not exist "portable_MIGPT_Full\requires\" mkdir "portable_MIGPT_Full\requires"

:: 下载所有依赖
echo [信息] 正在下载依赖包...
pip download -r requirements.txt -d "portable_MIGPT_Full\requires"

:: 创建一键启动脚本
echo @echo off > "portable_MIGPT_Full\一键启动MIGPT.bat"
echo chcp 65001 ^> nul >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo title MIGPT-易 一键启动器 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo. >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo echo 正在检查环境... >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo. >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo :: 检查Python >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo where python ^>nul 2^>nul >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo if %%ERRORLEVEL%% neq 0 ( >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo     echo 未检测到Python，请先安装Python 3.8或更高版本 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo     echo 您可以从 https://www.python.org/downloads/ 下载Python >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo     pause >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo     exit /b 1 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo ) >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo. >> "portable_MIGPT_Full\一键启动MIGPT.bat"

echo :: 安装依赖 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo echo 正在检查并安装依赖... >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo if exist requires\*.* ( >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo   pip install --no-index --find-links=requires -r requirements.txt >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo   echo 依赖安装完成！ >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo ) >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo. >> "portable_MIGPT_Full\一键启动MIGPT.bat"

echo :: 检查配置文件 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo if not exist config.json ( >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo     echo 未找到配置文件，将为您打开配置界面 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo     python config_gui.py >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo     if not exist config.json ( >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo         echo 配置未完成，无法启动程序 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo         pause >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo         exit /b 1 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo     ) >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo ) >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo. >> "portable_MIGPT_Full\一键启动MIGPT.bat"

echo :: 清理缓存 >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo if exist __pycache__ rmdir /s /q __pycache__ >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo. >> "portable_MIGPT_Full\一键启动MIGPT.bat"

echo echo 正在启动MIGPT-易... >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo python -m MIGPT >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo. >> "portable_MIGPT_Full\一键启动MIGPT.bat"
echo pause >> "portable_MIGPT_Full\一键启动MIGPT.bat"

echo.
echo =============================================
echo       完整版打包已完成！
echo =============================================
echo.
echo MIGPT-易完整版已创建在portable_MIGPT_Full文件夹中。
echo 用户使用时只需：
echo 1. 确保电脑已安装Python 3.8+
echo 2. 运行"一键启动MIGPT.bat"
echo 3. 程序会自动从本地安装所有依赖，无需联网
echo.
pause
goto menu

:exit_program
exit 