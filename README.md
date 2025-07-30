# 🚀 快速开始指南

## 三步启动 AI PDF Reader

### 步骤 1: 安装依赖
```bash
pip install -r requirements.txt
```

### 步骤 2: 启动应用
```bash
python main.py --api-key sk-your-deepseek-api-key
```

### 步骤 3: 打开浏览器
访问：http://localhost:7860

---

## 🔑 获取 API 密钥

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册账号并登录
3. 在 API Keys 页面创建新密钥
4. 复制密钥（格式：sk-xxxxxx）

---

## 📱 使用方法

1. **上传PDF** - 点击"上传PDF"按钮
2. **开始处理** - 点击"开始处理"等待完成  
3. **浏览内容** - 使用翻页按钮浏览
4. **AI问答** - 在右侧聊天框提问

---

## ⚡ 一键启动

### Windows 用户
```cmd
# 双击运行 start.bat 脚本
start.bat

# 或在命令行中执行
.\start.bat
```

### Linux/Mac 用户  
```bash
# 给脚本执行权限
chmod +x start.sh

# 运行启动脚本
./start.sh
```

> 💡 启动脚本会自动：
> - 检查 Python 环境
> - 创建虚拟环境
> - 安装依赖包
> - 配置 API 密钥
> - 启动应用服务

---

## 🛠️ 常用命令

```bash
# 基本启动
python main.py --api-key sk-your-deepseek-api-key

# 自定义端口
python main.py --api-key sk-xxx --port 8080

# 允许外部访问
python main.py --api-key sk-xxx --host 0.0.0.0

# 生成分享链接
python main.py --api-key sk-xxx --share

# 组合使用多个参数
python main.py --api-key sk-xxx --port 8080 --host 0.0.0.0 --share
```

---

## 📋 详细启动流程

### Windows 用户

#### 方法一：使用命令提示符 (CMD)
```cmd
# 1. 打开命令提示符，导航到项目目录
cd C:\path\to\python_ai\python_

# 2. 创建虚拟环境（推荐）
python -m venv venv

# 3. 激活虚拟环境
venv\Scripts\activate

# 4. 升级pip
python -m pip install --upgrade pip

# 5. 安装依赖包
pip install -r requirements.txt

# 6. 设置API密钥（临时）
set DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 7. 启动应用
python main.py
```

#### 方法二：使用PowerShell
```powershell
# 1. 打开PowerShell，导航到项目目录
cd C:\path\to\python_ai\python_

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 4. 安装依赖
pip install -r requirements.txt

# 5. 设置API密钥
$env:DEEPSEEK_API_KEY="sk-your-deepseek-api-key"

# 6. 启动应用
python main.py
```

### Linux/Mac 用户

#### 使用终端
```bash
# 1. 打开终端，导航到项目目录
cd /path/to/python_ai/python_

# 2. 创建虚拟环境（推荐）
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 升级pip
pip install --upgrade pip

# 5. 安装依赖包
pip install -r requirements.txt

# 6. 设置API密钥
export DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 7. 启动应用
python main.py
```

---

## 📝 环境变量配置

### Windows 永久配置
```cmd
# 使用setx命令永久设置
setx DEEPSEEK_API_KEY "sk-your-deepseek-api-key"

# 重启命令提示符后生效
```

### Linux/Mac 永久配置
```bash
# 添加到shell配置文件
echo 'export DEEPSEEK_API_KEY=sk-your-deepseek-api-key' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

---

## 🆘 遇到问题？

1. **端口被占用** → 更换端口：`--port 8080`
2. **API密钥错误** → 检查密钥格式和有效性
3. **依赖安装失败** → 尝试：`pip install --upgrade pip`
4. **无法访问** → 检查防火墙设置


