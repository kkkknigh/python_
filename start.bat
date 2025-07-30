@echo off
chcp 65001 >nul
title AI PDF Reader - 智能论文阅读器

echo.
echo ========================================
echo      AI PDF Reader - 智能论文阅读器
echo ========================================
echo.

REM 检查Python版本
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    echo 💡 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set python_version=%%i
echo ✅ Python版本: %python_version%

REM 检查pip
echo [2/6] 检查pip工具...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip工具未找到
    pause
    exit /b 1
)
echo ✅ pip工具正常

REM 检查依赖文件
echo [3/6] 检查项目文件...
if not exist "requirements.txt" (
    echo ❌ 未找到requirements.txt文件
    echo 💡 请确保在正确的项目目录中运行此脚本
    pause
    exit /b 1
)

if not exist "main.py" (
    echo ❌ 未找到main.py文件
    echo 💡 请确保在正确的项目目录中运行此脚本
    pause
    exit /b 1
)
echo ✅ 项目文件完整

REM 创建虚拟环境
echo [4/6] 准备Python环境...
if not exist "venv" (
    echo 🔧 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)

REM 升级pip
echo 🔧 升级pip...
python -m pip install --upgrade pip --quiet

REM 安装依赖包
echo [5/6] 安装依赖包...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ 依赖包安装失败
    echo 💡 尝试手动安装: pip install -r requirements.txt
    pause
    exit /b 1
)
echo ✅ 依赖包安装完成

REM 检查API密钥
echo [6/6] 配置API密钥...
if "%DEEPSEEK_API_KEY%"=="" (
    echo ⚠️  未检测到DEEPSEEK_API_KEY环境变量
    echo.
    echo 💡 获取API密钥步骤:
    echo    1. 访问 https://platform.deepseek.com/
    echo    2. 注册账号并登录
    echo    3. 在API Keys页面创建新密钥
    echo    4. 复制密钥（格式: sk-xxxxxx）
    echo.
    set /p api_key=🔑 请输入您的DeepSeek API密钥: 
    if "!api_key!"=="" (
        echo ❌ API密钥不能为空
        pause
        exit /b 1
    )
    set DEEPSEEK_API_KEY=!api_key!
    echo ✅ API密钥已设置
) else (
    echo ✅ API密钥已配置
)

REM 创建临时目录
echo 🔧 创建临时目录...
if not exist "temp" mkdir temp
if not exist "temp\html" mkdir temp\html
if not exist "temp\html\original" mkdir temp\html\original
if not exist "temp\html\translated" mkdir temp\html\translated
if not exist "temp\html\final" mkdir temp\html\final
if not exist "temp\picture" mkdir temp\picture
if not exist "temp\figures" mkdir temp\figures

echo.
echo ========================================
echo 🚀 启动AI PDF Reader
echo ========================================
echo 💻 访问地址: http://localhost:7860
echo 🛑 按 Ctrl+C 停止服务
echo ========================================
echo.

REM 启动应用
python main.py
if errorlevel 1 (
    echo.
    echo ❌ 应用启动失败
    echo 💡 请检查错误信息并重试
    pause
    exit /b 1
)

echo.
echo 👋 应用已停止运行
pause
