#gradio 论文阅读器



## 1. 功能



~~~mermaid
graph TD
A[用户上传] --> B[文档仓库]
B --> C1[单文档阅读]
C1 --> D[翻译]
C1 --> G[答疑]
C1 --> E[关键解析]
C1 --> F[拓展推荐]


B --> C2[知识图谱构建]
C2 --> H[知识向量存储]
H --> I[知识图谱可视化]
~~~

## 2. 实现路径



* 翻译

  * 上传文档后调用API进行整篇文章的翻译

* 答疑

  * 界面提供AI聊天框，针对文章内容与知识库内容进行答疑

* 关键解析

  * 上传文档后调用API分条解析文章关键内容
  * 界面可收缩

* 拓展推荐

  * 上传文章后调用API进行拓展论文推荐

  * 爬虫爬取对应论文后显示资源（不确定资源可获得性）

  * 界面可收缩

---

​    ### 知识图谱相关内容（不确定能否实现）

* 知识图谱构建

  * 根据文档由llm抽取主体-关系-客体：LangChain开源模型

    [参考链接](https://zhuanlan.zhihu.com/p/1919781127339620246)

    [官方文档]([LangChain Python API Reference — 🦜🔗 LangChain documentation](https://python.langchain.com/api_reference/))

* 知识向量存储

  * 抽取关系注入知识向量库：faiss

    [参考链接](https://blog.csdn.net/Lilith_0828/article/details/147294838)

    [官方文档](https://faiss.org.cn/)

* 知识图谱可视化

  * 从知识向量库中抽取实体，PyVis可视化
  
    ~~~python
    from pyvis.network import Network
    net = Network()
    # 添加节点（高亮FAISS结果）
    for node in subgraph_nodes:
        color = "red" if node["id"] in faiss_results else "blue"
        net.add_node(node["id"], label=node["name"], color=color)
    # 添加边
    for edge in subgraph_edges:
        net.add_edge(edge["source"], edge["target"], title=edge["type"])
    net.show("kg.html")  # 生成交互式HTML
    ~~~



##3. 组织架构

### 3.1. 项目目录结构

```
AiReader/
├── src/                      # 源代码
│   ├── ui/                   # 界面模块
|       ├── document_upload.py     # 上传文件界面
|       ├── document_read.py       # 论文阅读界面
|       ├── document_chat.py       # 答疑聊天界面
|       ├── block.py               # 可收缩框，打开为相关推荐和关键解析
|       └── ...                    # 知识图谱相关，不确定做不做
│   ├── api/                  # API 接口模块，对接LLM
|       ├── document_translate.py  # 文档翻译
|       ├── document_recommend.py  # 相关阅读推荐
|       └── document_analysize.py  # 文章关键解析
│   ├── knowledge_graph/      # 知识图谱模块
│   ├── document_process/  # 文档处理模块
|       ├── document_upload.py  # 文档上传与阅读
|       └── ...                 # 文档存储，对接知识图谱，不确定做不做
│   ├── main.py               # 主程序入口
├── docs/                     # 文档
├── data/                     # 数据文件
├── README.md                 # 说明文档
└── requirements.txt          # 依赖说明文件
```

### 3.2. 模块划分

*   **ui**: 负责用户界面，使用 Gradio 构建。
*   **api**: 负责调用各种 API，例如翻译，答疑，关键解析，拓展推荐等。
*   **document\_processing**: 负责文档的上传和存储。

* （**knowledge\_graph**）: 负责知识图谱的构建，存储和可视化。

### 3.3. 技术栈

*   Python
*   Gradio
*   OpenaiAPI
*   论文处理 (PDF文字阅读，图表处理，图片处理？)
    * PyMuPDF：文本，图片

知识图谱相关：

* LangChain
* faiss
* PyVis

### 3.4. 部署架构

*   本地部署