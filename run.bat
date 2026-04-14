@echo off
chcp 65001 >nul
echo ======================================
echo   绩效考核管理系统
echo ======================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 检查是否已安装依赖
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 📦 正在安装依赖包...
    pip install -r requirements.txt
    echo ✅ 依赖包安装完成
    echo.
)

REM 初始化数据库（如果不存在）
if not exist "performance_data.db" (
    echo 🔧 正在初始化数据库...
    python database.py
    echo.
)

echo 🚀 启动系统...
echo.
echo 访问地址: http://localhost:8501
echo 按 Ctrl+C 停止服务
echo.

REM 启动Streamlit
streamlit run app.py --server.port 8501 --server.address localhost

pause
