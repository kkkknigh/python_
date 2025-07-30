#!/bin/bash

# AI PDF Reader 启动脚本
# 支持 Linux 和 macOS

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_success() {
    print_message $GREEN "✅ $1"
}

print_error() {
    print_message $RED "❌ $1"
}

print_warning() {
    print_message $YELLOW "⚠️  $1"
}

print_info() {
    print_message $BLUE "🔧 $1"
}

echo ""
echo "========================================"
echo "    AI PDF Reader - 智能论文阅读器"
echo "========================================"
echo ""

# 1. 检查Python版本
print_info "[1/6] 检查Python环境..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "未找到Python，请先安装Python 3.8+"
    echo "💡 Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "💡 CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "💡 macOS: brew install python3"
    exit 1
fi

python_version=$($PYTHON_CMD --version 2>&1)
print_success "Python版本: $python_version"

# 2. 检查pip
print_info "[2/6] 检查pip工具..."
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    print_error "pip工具未找到"
    exit 1
fi
print_success "pip工具正常"

# 3. 检查项目文件
print_info "[3/6] 检查项目文件..."
if [ ! -f "requirements.txt" ]; then
    print_error "未找到requirements.txt文件"
    echo "💡 请确保在正确的项目目录中运行此脚本"
    exit 1
fi

if [ ! -f "main.py" ]; then
    print_error "未找到main.py文件"
    echo "💡 请确保在正确的项目目录中运行此脚本"
    exit 1
fi
print_success "项目文件完整"

# 4. 创建和激活虚拟环境
print_info "[4/6] 准备Python环境..."
if [ ! -d "venv" ]; then
    print_info "创建虚拟环境..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        print_error "虚拟环境创建失败"
        exit 1
    fi
    print_success "虚拟环境创建成功"
else
    print_success "虚拟环境已存在"
fi

print_info "激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    print_error "虚拟环境激活失败"
    exit 1
fi

# 升级pip
print_info "升级pip..."
pip install --upgrade pip --quiet

# 5. 安装依赖包
print_info "[5/6] 安装依赖包..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    print_error "依赖包安装失败"
    echo "💡 尝试手动安装: pip install -r requirements.txt"
    exit 1
fi
print_success "依赖包安装完成"

# 6. 配置API密钥
print_info "[6/6] 配置API密钥..."
if [ -z "$DEEPSEEK_API_KEY" ]; then
    print_warning "未检测到DEEPSEEK_API_KEY环境变量"
    echo ""
    echo "💡 获取API密钥步骤:"
    echo "   1. 访问 https://platform.deepseek.com/"
    echo "   2. 注册账号并登录"
    echo "   3. 在API Keys页面创建新密钥"
    echo "   4. 复制密钥（格式: sk-xxxxxx）"
    echo ""
    read -p "🔑 请输入您的DeepSeek API密钥: " api_key
    if [ -z "$api_key" ]; then
        print_error "API密钥不能为空"
        exit 1
    fi
    export DEEPSEEK_API_KEY="$api_key"
    print_success "API密钥已设置"
else
    print_success "API密钥已配置"
fi

# 创建临时目录
print_info "创建临时目录..."
mkdir -p temp/{html/{original,translated,final},picture,figures}

echo ""
echo "========================================"
echo "🚀 启动AI PDF Reader"
echo "========================================"
echo "💻 访问地址: http://localhost:7860"
echo "🛑 按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动应用
$PYTHON_CMD main.py
if [ $? -ne 0 ]; then
    echo ""
    print_error "应用启动失败"
    echo "💡 请检查错误信息并重试"
    exit 1
fi

echo ""
print_info "👋 应用已停止运行"
