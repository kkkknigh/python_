# 🚀 一键启动指南

## Windows 用户

### 方法一：双击启动（推荐）
1. 双击 `start.bat` 文件
2. 按提示输入 DeepSeek API 密钥
3. 等待自动安装依赖和启动
4. 在浏览器中访问 http://localhost:7860

### 方法二：命令行启动
```cmd
# 打开命令提示符，切换到项目目录
cd C:\path\to\python_ai\python_

# 运行启动脚本
start.bat

# 或者手动启动
pip install -r requirements.txt
python main.py --api-key sk-your-deepseek-api-key
```

## Linux/Mac 用户

### 方法一：脚本启动（推荐）
```bash
# 在终端中切换到项目目录
cd /path/to/python_ai/python_

# 给脚本执行权限
chmod +x start.sh

# 运行启动脚本
./start.sh
```

### 方法二：手动启动
```bash
# 安装依赖
pip3 install -r requirements.txt

# 设置API密钥
export DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 启动应用
python3 main.py
```

## 🔑 获取 DeepSeek API 密钥

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册账号并登录
3. 进入 "API Keys" 页面
4. 点击 "Create API Key" 创建新密钥
5. 复制生成的密钥（格式：sk-xxxxxx）

## ✅ 启动成功标志

看到以下信息表示启动成功：
```
Running on local URL:  http://127.0.0.1:7860
```

## 🛠️ 故障排除

### Python 环境问题
```bash
# 检查 Python 版本（需要 3.8+）
python --version

# 如果提示找不到 python 命令，尝试
python3 --version
```

### 依赖安装问题
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像加速安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 端口被占用
```bash
# 使用其他端口启动
python main.py --api-key sk-xxx --port 8080
```

### API 密钥问题
- 确认密钥格式正确（以 sk- 开头）
- 检查密钥是否有效且有余额
- 确认网络连接正常

## 📱 使用流程

1. **上传 PDF** - 点击"上传PDF"按钮选择文件
2. **开始处理** - 点击"开始处理"按钮，等待完成
3. **浏览内容** - 使用"上一页"/"下一页"浏览文档
4. **AI 问答** - 在右侧聊天框中提问

## 🎯 注意事项

- 首次启动会自动下载安装依赖包，可能需要几分钟
- 处理大型 PDF 文件需要较长时间，请耐心等待
- 建议使用高质量、文字清晰的 PDF 文件
- 需要稳定的网络连接用于 AI API 调用

---

如遇到其他问题，请查看 `README.md` 中的详细说明。
