#!/bin/bash

echo "======================================"
echo "  绩效考核管理系统"
echo "======================================"
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.8或更高版本"
    exit 1
fi

# 检查是否已安装依赖
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📦 正在安装依赖包..."
    pip3 install -r requirements.txt --break-system-packages
    echo "✅ 依赖包安装完成"
    echo ""
fi

# 初始化数据库（如果不存在）
if [ ! -f "performance_data.db" ]; then
    echo "🔧 正在初始化数据库..."
    python3 database.py
    echo ""
fi

echo "🚀 启动系统..."
echo ""
echo "访问地址: http://localhost:8501"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动Streamlit
streamlit run app.py --server.port 8501 --server.address localhost
