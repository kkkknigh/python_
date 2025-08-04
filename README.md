# AI Reader

一个PDF学术论文处理工具，支持图片提取、文本翻译、智能问答和结构化展示。

### 快速开始

```bash
cd python_
pip install -r requirements.txt
python main.py
```

### API密钥配置

```bash
# 方式1: 命令行参数
python main.py --apikey <Your Api Key>

# 方式2: 环境变量
export DEEPSEEK_API_KEY=<Your Api Key>
python main.py

# 方式3: 修改代码中的全局变量 DEEPSEEK_API_KEY
```

