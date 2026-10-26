"""技术名词典：让程序"认识"常见的框架、库和工具。

【给初学者：为什么需要一张词典？】
仓库里能读到的东西只有"名字"：requirements.txt 里写着 `fastapi==0.115.0`，
package.json 里写着 `"react": "^18.3.1"`。程序本身并不知道 FastAPI 是"后端框架"。
所以我们要准备一张表：名字 -> 分类 + 一句话说明。这就是本文件。

有了它，扫描器才能把一堆零散的依赖，整理成网页上按分类展示的"技术栈"。
词典当然是越全越好，但也不可能穷尽；遇到不认识的名字，扫描器会把它放进
"其他依赖"，不会丢。

【匹配规则】
1. 先做精确匹配：忽略大小写，把下划线统一成短横线
   （Python 包名 psycopg2_binary 和 psycopg2-binary 视为同一个）。
2. 再尝试前缀匹配：比如 spring-boot-starter-web 应该归到 Spring Boot，
   @nestjs/common 应该归到 NestJS，github.com/gin-gonic/gin/v2 归到 Gin。
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 分类的顺序，也是网页上展示的顺序（从"语言/框架"到"其他"）。
CATEGORIES: tuple[str, ...] = (
    "编程语言",
    "前端框架",
    "后端框架",
    "AI & Agent",
    "数据库",
    "缓存与消息",
    "基础设施与运维",
    "测试与质量",
    "构建与工具链",
    "数据科学",
    "监控与观测",
    "其他依赖",
)

CATEGORY_ICONS = {
    "编程语言": "🧩",
    "前端框架": "🎨",
    "后端框架": "🧱",
    "AI & Agent": "🤖",
    "数据库": "🗄️",
    "缓存与消息": "📮",
    "基础设施与运维": "🐳",
    "测试与质量": "🧪",
    "构建与工具链": "🛠️",
    "数据科学": "📊",
    "监控与观测": "📈",
    "其他依赖": "📦",
}

# 这些名字太"通用"，出现在依赖里通常只是传递依赖或构建元数据，展示出来意义不大。
NOISE_PACKAGES = {
    "pip",
    "setuptools",
    "wheel",
    "poetry-core",
    "hatchling",
    "flit-core",
    "build",
    "twine",
    "setuptools-scm",
    "packaging",
    "typing-extensions",
    "typing_extensions",
    "certifi",
    "charset-normalizer",
    "idna",
    "urllib3",
    "six",
    "pyparsing",
    "attrs",
    "iniconfig",
    "pluggy",
    "colorama",
    "node-gyp",
    "eslint-config-react-app",
    "eslint-plugin-react",
    "eslint-plugin-import",
    "prettier-plugin-tailwindcss",
    "rimraf",
    "cross-env",
    "dotenv-cli",
    "maven-compiler-plugin",
    "maven-surefire-plugin",
    "spring-boot-maven-plugin",
}


@dataclass(frozen=True)
class TechSpec:
    """一项技术的"档案"。"""

    name: str            # 展示名，例如 FastAPI
    category: str        # 分类，必须是 CATEGORIES 里的一个
    aliases: tuple[str, ...]  # 可能出现的写法（依赖名 / 导入名 / 镜像名）
    hint: str = ""       # 一句话说明，用于兜底生成"职责"描述
    ecosystem: str = ""  # 偏好生态：python/js/java/go/rust/docker/any，留空表示都行


def T(name: str, category: str, aliases: tuple[str, ...], hint: str = "", ecosystem: str = "") -> TechSpec:
    return TechSpec(name=name, category=category, aliases=aliases, hint=hint, ecosystem=ecosystem)


# ============================================================================
# 词典正文。阅读建议：不用背，先浏览分类，用到时再回来查。
# ============================================================================
CATALOG: list[TechSpec] = [
    # ---------------------------------------------------------------- 编程语言
    T("Python", "编程语言", ("python", "python3", "cpython"), "解释型语言，AI/后端/脚本的主力"),
    T("JavaScript", "编程语言", ("javascript", "js", "ecmascript"), "浏览器和 Node.js 的脚本语言"),
    T("TypeScript", "编程语言", ("typescript", "ts"), "给 JavaScript 加上类型系统的语言"),
    T("Java", "编程语言", ("java", "openjdk", "jdk", "temurin"), "大型企业后端常用语言"),
    T("Go", "编程语言", ("go", "golang"), "编译快、并发强的后端语言"),
    T("Rust", "编程语言", ("rust",), "内存安全、性能接近 C 的语言"),
    T("C", "编程语言", ("c",), "底层系统编程语言"),
    T("C++", "编程语言", ("c++", "cpp", "cplusplus"), "高性能系统与游戏开发语言"),
    T("C#", "编程语言", ("csharp", "c#", "dotnet", ".net"), "微软生态的主力语言"),
    T("PHP", "编程语言", ("php",), "传统 Web 开发语言"),
    T("Ruby", "编程语言", ("ruby",), "注重开发效率的语言，Rails 生态"),
    T("Kotlin", "编程语言", ("kotlin",), "JVM 上的现代语言，Android 首选"),
    T("Swift", "编程语言", ("swift",), "苹果生态开发语言"),
    T("Scala", "编程语言", ("scala",), "JVM 上的函数式语言，大数据常用"),
    T("Dart", "编程语言", ("dart",), "Flutter 使用的语言"),
    T("Shell", "编程语言", ("shell", "bash", "sh"), "命令行脚本"),

    # ---------------------------------------------------------------- 前端
    T("React", "前端框架", ("react", "react-dom", "react-router", "react-router-dom"), "组件化前端框架，生态最大", "js"),
    T("Next.js", "前端框架", ("next", "next.js"), "基于 React 的全栈框架，支持 SSR/SSG", "js"),
    T("Vue.js", "前端框架", ("vue", "vue-router", "vuex", "pinia"), "渐进式前端框架，国内使用广泛", "js"),
    T("Nuxt", "前端框架", ("nuxt", "nuxt3"), "基于 Vue 的全栈框架", "js"),
    T("Angular", "前端框架", ("@angular/core", "@angular/cli", "angular"), "企业级前端框架，自带完整方案", "js"),
    T("Svelte", "前端框架", ("svelte", "@sveltejs/kit", "sveltekit"), "编译期优化的前端框架", "js"),
    T("SolidJS", "前端框架", ("solid-js", "solid"), "细粒度响应的前端框架", "js"),
    T("Preact", "前端框架", ("preact",), "体积很小的 React 替代品", "js"),
    T("Astro", "前端框架", ("astro",), "内容优先的静态站点框架", "js"),
    T("Remix", "前端框架", ("@remix-run/react", "remix"), "基于 React 的全栈框架", "js"),
    T("Electron", "前端框架", ("electron", "electron-builder"), "用 Web 技术写桌面应用", "js"),
    T("Tauri", "前端框架", ("@tauri-apps/api", "tauri"), "Rust 内核的轻量桌面应用框架", "js"),
    T("uni-app", "前端框架", ("@dcloudio/uni-app", "uni-app"), "一套代码编译到多端（小程序/App）", "js"),
    T("Taro", "前端框架", ("@tarojs/taro", "taro"), "多端小程序开发框架", "js"),
    T("jQuery", "前端框架", ("jquery",), "老牌 DOM 操作库", "js"),
    T("Tailwind CSS", "前端框架", ("tailwindcss",), "原子化 CSS 框架", "js"),
    T("Bootstrap", "前端框架", ("bootstrap",), "经典 CSS 组件库", "js"),
    T("Ant Design", "前端框架", ("antd", "@ant-design/icons"), "企业级 React 组件库", "js"),
    T("Element Plus", "前端框架", ("element-plus", "element-ui"), "Vue 3 组件库", "js"),
    T("Material UI", "前端框架", ("@mui/material", "@material-ui/core"), "Google Material 风格 React 组件库", "js"),
    T("Vuetify", "前端框架", ("vuetify",), "Vue 的 Material 组件库", "js"),
    T("Sass", "前端框架", ("sass", "node-sass"), "CSS 预处理器", "js"),
    T("Less", "前端框架", ("less",), "CSS 预处理器", "js"),
    T("styled-components", "前端框架", ("styled-components", "@emotion/react"), "CSS-in-JS 样式方案", "js"),
    T("Three.js", "前端框架", ("three",), "浏览器 3D 渲染库", "js"),
    T("ECharts", "前端框架", ("echarts",), "百度开源的图表库", "js"),
    T("Chart.js", "前端框架", ("chart.js", "chartjs"), "轻量图表库", "js"),
    T("D3.js", "前端框架", ("d3",), "数据可视化底层库", "js"),
    T("Redux", "前端框架", ("redux", "@reduxjs/toolkit", "react-redux"), "React 状态管理", "js"),
    T("Zustand", "前端框架", ("zustand",), "轻量 React 状态管理", "js"),
    T("MobX", "前端框架", ("mobx", "mobx-react"), "响应式状态管理", "js"),
    T("Axios", "前端框架", ("axios",), "常用 HTTP 请求库", "js"),
    T("Lodash", "前端框架", ("lodash",), "JavaScript 工具函数库", "js"),
    T("Day.js", "前端框架", ("dayjs",), "轻量日期库", "js"),

    # ---------------------------------------------------------------- 后端
    T("FastAPI", "后端框架", ("fastapi",), "高性能 Python Web 框架，自动生成接口文档", "python"),
    T("Flask", "后端框架", ("flask",), "轻量 Python Web 框架", "python"),
    T("Django", "后端框架", ("django",), "自带 ORM/后台的 Python 全栈框架", "python"),
    T("Django REST Framework", "后端框架", ("djangorestframework", "django-rest-framework", "rest-framework"), "Django 的 REST API 扩展", "python"),
    T("Starlette", "后端框架", ("starlette",), "FastAPI 底层的异步 Web 框架", "python"),
    T("Sanic", "后端框架", ("sanic",), "异步 Python Web 框架", "python"),
    T("Litestar", "后端框架", ("litestar",), "现代异步 Python Web 框架", "python"),
    T("Tornado", "后端框架", ("tornado",), "异步 Web 框架，擅长长连接", "python"),
    T("Aiohttp", "后端框架", ("aiohttp",), "异步 HTTP 客户端/服务端", "python"),
    T("Uvicorn", "后端框架", ("uvicorn", "uvicorn-standard"), "ASGI 服务器，常用来运行 FastAPI/Starlette", "python"),
    T("Gunicorn", "后端框架", ("gunicorn",), "常用的 Python WSGI 服务器", "python"),
    T("Pydantic", "后端框架", ("pydantic", "pydantic-settings"), "数据校验与配置管理，FastAPI 的好搭档", "python"),
    T("Express", "后端框架", ("express",), "Node.js 最经典的 Web 框架", "js"),
    T("Koa", "后端框架", ("koa",), "更轻量的 Node.js Web 框架", "js"),
    T("NestJS", "后端框架", ("@nestjs/core", "@nestjs/common", "nestjs"), "Node.js 的企业级框架，写法类似 Spring", "js"),
    T("Fastify", "后端框架", ("fastify",), "高性能 Node.js Web 框架", "js"),
    T("Hapi", "后端框架", ("@hapi/hapi", "hapi"), "配置驱动的 Node.js 框架", "js"),
    T("Hono", "后端框架", ("hono",), "可在边缘运行时运行的轻量框架", "js"),
    T("Spring Boot", "后端框架", ("spring-boot", "spring-boot-starter-web", "spring-boot-starter", "org.springframework.boot"), "Java 生态最主流的快速开发框架", "java"),
    T("Spring Framework", "后端框架", ("spring-core", "spring-web", "spring-context", "org.springframework"), "Spring 基础框架", "java"),
    T("Spring Cloud", "后端框架", ("spring-cloud", "org.springframework.cloud"), "微服务治理套件", "java"),
    T("Spring Security", "后端框架", ("spring-security", "org.springframework.security"), "认证与授权框架", "java"),
    T("MyBatis", "数据库", ("mybatis", "mybatis-spring-boot-starter", "org.mybatis"), "Java 的 SQL 映射 ORM", "java"),
    T("MyBatis-Plus", "数据库", ("mybatis-plus", "com.baomidou"), "MyBatis 增强工具", "java"),
    T("Hibernate", "数据库", ("hibernate-core", "org.hibernate", "hibernate"), "Java ORM 标准实现", "java"),
    T("JPA", "数据库", ("spring-boot-starter-data-jpa", "jakarta.persistence", "javax.persistence"), "Java 持久化规范", "java"),
    T("Gin", "后端框架", ("github.com/gin-gonic/gin", "gin-gonic"), "Go 最流行的 Web 框架", "go"),
    T("Echo", "后端框架", ("github.com/labstack/echo", "labstack/echo"), "Go Web 框架", "go"),
    T("Fiber", "后端框架", ("github.com/gofiber/fiber", "gofiber/fiber"), "Express 风格的 Go 框架", "go"),
    T("Chi", "后端框架", ("github.com/go-chi/chi", "go-chi/chi"), "轻量 Go 路由库", "go"),
    T("Beego", "后端框架", ("github.com/beego/beego", "beego"), "Go 全栈框架", "go"),
    T("Kratos", "后端框架", ("github.com/go-kratos/kratos", "go-kratos"), "B站开源的 Go 微服务框架", "go"),
    T("Actix Web", "后端框架", ("actix-web", "actix_web"), "高性能 Rust Web 框架", "rust"),
    T("Axum", "后端框架", ("axum",), "Tokio 官方 Rust Web 框架", "rust"),
    T("Rocket", "后端框架", ("rocket",), "易上手的 Rust Web 框架", "rust"),
    T("ASP.NET Core", "后端框架", ("microsoft.aspnetcore", "aspnetcore", "asp.net"), "微软的跨平台 Web 框架", "any"),
    T("Entity Framework Core", "数据库", ("microsoft.entityframeworkcore", "entityframework"), "微软的 ORM", "any"),
    T("Laravel", "后端框架", ("laravel/framework", "laravel"), "PHP 最流行的全栈框架", "any"),
    T("Symfony", "后端框架", ("symfony",), "PHP 组件化框架", "any"),
    T("Ruby on Rails", "后端框架", ("rails", "railties"), "约定优于配置的 Ruby 框架", "any"),
    T("Sinatra", "后端框架", ("sinatra",), "轻量 Ruby Web 框架", "any"),
    T("gRPC", "后端框架", ("grpc", "grpcio", "google.golang.org/grpc", "@grpc/grpc-js"), "高性能 RPC 通信框架", "any"),
    T("GraphQL", "后端框架", ("graphql", "graphene", "strawberry-graphql", "apollo-server", "@apollo/server"), "按需查询的 API 规范", "any"),

    # ---------------------------------------------------------------- AI & Agent
    T("LangChain", "AI & Agent", ("langchain", "langchain-core", "langchain-community", "langchain-openai", "langchain-deepseek", "langchain-anthropic", "langchain-text-splitters"), "构建大模型应用的框架：链、工具、Agent", "python"),
    T("LangGraph", "AI & Agent", ("langgraph", "langgraph-checkpoint", "langgraph-prebuilt", "langgraph-sdk"), "用「图」编排有状态 Agent 的框架", "python"),
    T("Deep Agents", "AI & Agent", ("deepagents", "deep-agents"), "LangChain 官方的深度任务 Agent 框架", "python"),
    T("LangSmith", "监控与观测", ("langsmith",), "LangChain 官方的调用追踪与评测平台", "python"),
    T("OpenAI SDK", "AI & Agent", ("openai",), "OpenAI 官方 Python/JS SDK", "any"),
    T("Anthropic SDK", "AI & Agent", ("anthropic",), "Claude 模型官方 SDK", "any"),
    T("Google GenAI", "AI & Agent", ("google-genai", "google-generativeai"), "Google Gemini 模型 SDK", "any"),
    T("Ollama", "AI & Agent", ("ollama", "langchain-ollama"), "本地运行开源大模型的工具", "any"),
    T("LlamaIndex", "AI & Agent", ("llama-index", "llama-index-core", "llamaindex"), "专注 RAG 的数据框架", "python"),
    T("CrewAI", "AI & Agent", ("crewai", "crewai-tools"), "多 Agent 协作框架", "python"),
    T("AutoGen", "AI & Agent", ("autogen", "pyautogen", "autogen-agentchat"), "微软的多 Agent 对话框架", "python"),
    T("PydanticAI", "AI & Agent", ("pydantic-ai", "pydantic_ai"), "Pydantic 团队出品的 Agent 框架", "python"),
    T("MCP", "AI & Agent", ("mcp", "modelcontextprotocol", "@modelcontextprotocol/sdk"), "模型上下文协议，给 Agent 接工具的标准", "any"),
    T("Transformers", "AI & Agent", ("transformers",), "Hugging Face 的预训练模型库", "python"),
    T("PyTorch", "AI & Agent", ("torch", "pytorch", "torchvision"), "深度学习框架", "python"),
    T("TensorFlow", "AI & Agent", ("tensorflow", "tensorflow-gpu"), "Google 的深度学习框架", "python"),
    T("Keras", "AI & Agent", ("keras",), "高层神经网络 API", "python"),
    T("JAX", "AI & Agent", ("jax", "jaxlib", "flax"), "函数式数值计算框架", "python"),
    T("scikit-learn", "数据科学", ("scikit-learn", "sklearn"), "经典机器学习算法库", "python"),
    T("XGBoost", "数据科学", ("xgboost",), "梯度提升树模型", "python"),
    T("LightGBM", "数据科学", ("lightgbm",), "微软的梯度提升树模型", "python"),
    T("ONNX Runtime", "AI & Agent", ("onnxruntime", "onnxruntime-gpu"), "跨平台模型推理引擎", "python"),
    T("Sentence Transformers", "AI & Agent", ("sentence-transformers",), "文本向量化模型库", "python"),
    T("Hugging Face Hub", "AI & Agent", ("huggingface-hub",), "模型/数据集托管平台客户端", "python"),
    T("vLLM", "AI & Agent", ("vllm",), "高吞吐大模型推理引擎", "python"),
    T("Chroma", "AI & Agent", ("chromadb", "chroma"), "轻量向量数据库，常做 RAG", "python"),
    T("FAISS", "AI & Agent", ("faiss-cpu", "faiss-gpu", "faiss"), "Facebook 的向量检索库", "python"),
    T("Milvus", "AI & Agent", ("pymilvus", "milvus"), "分布式向量数据库", "python"),
    T("Pinecone", "AI & Agent", ("pinecone", "pinecone-client"), "托管向量数据库", "python"),
    T("Qdrant", "AI & Agent", ("qdrant-client", "qdrant"), "Rust 写的向量数据库", "python"),
    T("Weaviate", "AI & Agent", ("weaviate-client", "weaviate"), "带混合检索的向量数据库", "python"),
    T("pgvector", "AI & Agent", ("pgvector",), "PostgreSQL 的向量检索扩展", "python"),
    T("Tavily", "AI & Agent", ("tavily-python", "langchain-tavily", "tavily"), "为 Agent 设计的联网搜索 API", "python"),

    # ---------------------------------------------------------------- 数据库
    T("PostgreSQL", "数据库", ("postgres", "postgresql", "psycopg2", "psycopg2-binary", "psycopg", "asyncpg", "pg8000", "org.postgresql"), "功能强大的开源关系型数据库", "any"),
    T("MySQL", "数据库", ("mysql", "mysqlclient", "pymysql", "mysql-connector-python", "mysql-connector-java", "mysql2", "mysql-connector"), "最流行的开源关系型数据库", "any"),
    T("MariaDB", "数据库", ("mariadb",), "MySQL 的开源分支", "any"),
    T("SQLite", "数据库", ("sqlite", "sqlite3", "better-sqlite3", "aiosqlite"), "单文件嵌入式数据库", "any"),
    T("MongoDB", "数据库", ("mongodb", "pymongo", "motor", "mongo", "go.mongodb.org/mongo-driver", "github.com/mongodb/mongo-go-driver"), "文档型 NoSQL 数据库", "any"),
    T("Elasticsearch", "数据库", ("elasticsearch", "@elastic/elasticsearch", "elastic"), "全文检索与日志分析引擎", "any"),
    T("ClickHouse", "数据库", ("clickhouse-driver", "clickhouse-connect", "clickhouse"), "列式分析型数据库", "any"),
    T("Apache Cassandra", "数据库", ("cassandra-driver", "cassandra"), "高可用宽列数据库", "any"),
    T("Neo4j", "数据库", ("neo4j", "neo4j-driver"), "图数据库", "any"),
    T("InfluxDB", "数据库", ("influxdb", "influxdb-client"), "时序数据库", "any"),
    T("Oracle Database", "数据库", ("oracledb", "cx-oracle", "oracle"), "商业关系型数据库", "any"),
    T("SQL Server", "数据库", ("pyodbc", "mssql", "sqlserver"), "微软关系型数据库", "any"),
    T("SQLAlchemy", "数据库", ("sqlalchemy",), "Python 最常用的 ORM", "python"),
    T("Alembic", "数据库", ("alembic",), "SQLAlchemy 的数据库迁移工具", "python"),
    T("Peewee", "数据库", ("peewee",), "轻量 Python ORM", "python"),
    T("Tortoise ORM", "数据库", ("tortoise-orm", "tortoise"), "异步 Python ORM", "python"),
    T("Prisma", "数据库", ("prisma", "@prisma/client"), "类型安全的 Node.js ORM", "js"),
    T("Sequelize", "数据库", ("sequelize",), "Node.js 经典 ORM", "js"),
    T("TypeORM", "数据库", ("typeorm",), "TypeScript ORM", "js"),
    T("Mongoose", "数据库", ("mongoose",), "MongoDB 的 Node.js 建模工具", "js"),
    T("Drizzle ORM", "数据库", ("drizzle-orm", "drizzle-kit"), "轻量 TypeScript ORM", "js"),
    T("GORM", "数据库", ("gorm.io/gorm", "gorm"), "Go 最流行的 ORM", "go"),
    T("Diesel", "数据库", ("diesel",), "Rust ORM", "rust"),
    T("SQLx", "数据库", ("sqlx",), "Rust 异步 SQL 工具", "rust"),

    # ---------------------------------------------------------------- 缓存与消息
    T("Redis", "缓存与消息", ("redis", "aioredis", "ioredis", "redis-py", "redis.asyncio", "rediscache", "redisclient", "strictredis", "rediscluster", "redis-om", "redisjson", "redisearch", "redisvl", "spring-boot-starter-data-redis", "github.com/redis/go-redis", "github.com/go-redis/redis"), "内存缓存，也常用作消息队列/会话存储", "any"),
    T("Apache Kafka", "缓存与消息", ("kafka", "kafka-python", "confluent-kafka", "spring-kafka", "kafkajs"), "高吞吐分布式消息队列", "any"),
    T("RabbitMQ", "缓存与消息", ("pika", "amqp", "amqplib", "spring-boot-starter-amqp", "rabbitmq"), "老牌消息队列", "any"),
    T("Celery", "缓存与消息", ("celery",), "Python 分布式任务队列", "python"),
    T("RQ", "缓存与消息", ("rq",), "基于 Redis 的简单任务队列", "python"),
    T("Dramatiq", "缓存与消息", ("dramatiq",), "Python 任务队列", "python"),
    T("BullMQ", "缓存与消息", ("bullmq", "bull"), "Node.js 任务队列", "js"),
    T("NATS", "缓存与消息", ("nats", "nats-py", "nats.js"), "轻量云原生消息系统", "any"),
    T("Apache Pulsar", "缓存与消息", ("pulsar-client", "pulsar"), "下一代分布式消息平台", "any"),
    T("RocketMQ", "缓存与消息", ("rocketmq", "rocketmq-client", "rocketmq-spring-boot-starter"), "阿里开源的消息队列", "any"),
    T("ZeroMQ", "缓存与消息", ("pyzmq", "zmq", "zeromq"), "嵌入式消息库", "any"),

    # ---------------------------------------------------------------- 基础设施
    T("Docker", "基础设施与运维", ("docker", "dockerfile"), "容器化打包与运行", "any"),
    T("Docker Compose", "基础设施与运维", ("docker-compose", "docker compose"), "用 YAML 编排多个容器", "any"),
    T("Kubernetes", "基础设施与运维", ("kubernetes", "k8s", "kube"), "容器编排平台", "any"),
    T("Helm", "基础设施与运维", ("helm",), "Kubernetes 的包管理工具", "any"),
    T("Terraform", "基础设施与运维", ("terraform",), "基础设施即代码（IaC）工具", "any"),
    T("Ansible", "基础设施与运维", ("ansible",), "自动化配置管理工具", "any"),
    T("Nginx", "基础设施与运维", ("nginx",), "高性能反向代理与静态资源服务器", "any"),
    T("GitHub Actions", "基础设施与运维", ("github-actions", "github actions"), "GitHub 自带 CI/CD", "any"),
    T("GitLab CI", "基础设施与运维", ("gitlab-ci", "gitlab ci"), "GitLab 的 CI/CD", "any"),
    T("Jenkins", "基础设施与运维", ("jenkins",), "老牌持续集成服务器", "any"),
    T("Argo CD", "基础设施与运维", ("argocd", "argo-cd", "argo cd"), "Kubernetes 的 GitOps 发布工具", "any"),
    T("MinIO", "基础设施与运维", ("minio", "minio-client"), "兼容 S3 的对象存储", "any"),
    T("AWS SDK", "基础设施与运维", ("boto3", "aws-sdk", "@aws-sdk/client-s3", "aws-sdk-go"), "亚马逊云服务 SDK", "any"),
    T("Azure SDK", "基础设施与运维", ("azure", "@azure/identity", "azure-sdk"), "微软云服务 SDK", "any"),
    T("Google Cloud SDK", "基础设施与运维", ("google-cloud", "@google-cloud/storage"), "谷歌云服务 SDK", "any"),
    T("Supabase", "基础设施与运维", ("supabase", "@supabase/supabase-js"), "开源的 Firebase 替代品", "any"),
    T("Firebase", "基础设施与运维", ("firebase", "firebase-admin"), "Google 的 BaaS 平台", "any"),
    T("Vercel", "基础设施与运维", ("vercel",), "前端部署平台", "any"),
    T("Cloudflare Workers", "基础设施与运维", ("wrangler", "cloudflare-workers"), "边缘计算运行时", "any"),
    T("Node.js", "基础设施与运维", ("node", "nodejs", "node.js"), "JavaScript 服务端运行时", "any"),

    # ---------------------------------------------------------------- 测试与质量
    T("pytest", "测试与质量", ("pytest", "pytest-asyncio", "pytest-cov"), "Python 最常用的测试框架", "python"),
    T("JUnit", "测试与质量", ("junit", "junit-jupiter", "org.junit"), "Java 测试框架", "java"),
    T("TestNG", "测试与质量", ("testng",), "Java 测试框架", "java"),
    T("Mockito", "测试与质量", ("mockito", "org.mockito"), "Java Mock 框架", "java"),
    T("Jest", "测试与质量", ("jest", "ts-jest"), "JavaScript 测试框架", "js"),
    T("Vitest", "测试与质量", ("vitest",), "基于 Vite 的测试框架", "js"),
    T("Mocha", "测试与质量", ("mocha",), "Node.js 测试框架", "js"),
    T("Chai", "测试与质量", ("chai",), "断言库", "js"),
    T("Cypress", "测试与质量", ("cypress",), "端到端测试框架", "js"),
    T("Playwright", "测试与质量", ("playwright", "@playwright/test"), "浏览器自动化测试", "any"),
    T("Selenium", "测试与质量", ("selenium", "selenium-webdriver"), "老牌浏览器自动化工具", "any"),
    T("Locust", "测试与质量", ("locust",), "Python 压力测试工具", "python"),
    T("k6", "测试与质量", ("k6",), "现代负载测试工具", "any"),
    T("Ruff", "测试与质量", ("ruff",), "极快的 Python 代码检查器", "python"),
    T("mypy", "测试与质量", ("mypy",), "Python 静态类型检查", "python"),
    T("Black", "测试与质量", ("black",), "Python 代码格式化工具", "python"),
    T("Flake8", "测试与质量", ("flake8",), "Python 代码风格检查", "python"),
    T("ESLint", "测试与质量", ("eslint",), "JavaScript 代码检查", "js"),
    T("Prettier", "测试与质量", ("prettier",), "前端代码格式化", "js"),
    T("SonarQube", "测试与质量", ("sonarqube", "sonar-scanner"), "代码质量平台", "any"),

    # ---------------------------------------------------------------- 构建与工具链
    T("Maven", "构建与工具链", ("maven", "org.apache.maven"), "Java 项目构建与依赖管理", "java"),
    T("Gradle", "构建与工具链", ("gradle", "org.gradle"), "灵活的 JVM 构建工具", "java"),
    T("npm", "构建与工具链", ("npm",), "Node.js 包管理器", "js"),
    T("pnpm", "构建与工具链", ("pnpm",), "更省磁盘的 Node.js 包管理器", "js"),
    T("Yarn", "构建与工具链", ("yarn",), "Node.js 包管理器", "js"),
    T("Vite", "构建与工具链", ("vite", "@vitejs/plugin-react", "@vitejs/plugin-vue"), "极快的前端构建工具", "js"),
    T("Webpack", "构建与工具链", ("webpack", "webpack-cli", "webpack-dev-server"), "经典前端打包工具", "js"),
    T("Rollup", "构建与工具链", ("rollup",), "库打包工具", "js"),
    T("esbuild", "构建与工具链", ("esbuild",), "极快的 JS 打包器", "js"),
    T("Babel", "构建与工具链", ("@babel/core", "babel-loader", "@babel/preset-env"), "JavaScript 编译器", "js"),
    T("Poetry", "构建与工具链", ("poetry",), "Python 依赖与打包管理", "python"),
    T("uv", "构建与工具链", ("uv",), "极快的 Python 包管理器", "python"),
    T("Pipenv", "构建与工具链", ("pipenv",), "Python 虚拟环境管理", "python"),
    T("Conda", "构建与工具链", ("conda",), "跨语言包与环境管理", "python"),
    T("CMake", "构建与工具链", ("cmake",), "C/C++ 跨平台构建", "any"),
    T("Make", "构建与工具链", ("make", "makefile"), "经典构建工具", "any"),
    T("Bazel", "构建与工具链", ("bazel",), "Google 的大规模构建系统", "any"),
    T("Cargo", "构建与工具链", ("cargo",), "Rust 的构建与包管理", "rust"),
    T("Nx", "构建与工具链", ("nx",), "前端多包仓库构建系统", "js"),
    T("Turborepo", "构建与工具链", ("turbo", "turborepo"), "前端多包仓库构建缓存", "js"),
    T("Lerna", "构建与工具链", ("lerna",), "多包仓库管理工具", "js"),
    T("python-dotenv", "构建与工具链", ("python-dotenv", "dotenv"), "从 .env 读取配置", "python"),
    T("Jupyter", "数据科学", ("jupyter", "notebook", "jupyterlab", "ipykernel"), "交互式笔记本环境", "python"),

    # ---------------------------------------------------------------- 数据科学
    T("NumPy", "数据科学", ("numpy",), "Python 数值计算基础库", "python"),
    T("Pandas", "数据科学", ("pandas",), "表格数据处理库", "python"),
    T("SciPy", "数据科学", ("scipy",), "科学计算库", "python"),
    T("Matplotlib", "数据科学", ("matplotlib",), "Python 绘图库", "python"),
    T("Seaborn", "数据科学", ("seaborn",), "统计图表库", "python"),
    T("Plotly", "数据科学", ("plotly",), "交互式图表库", "python"),
    T("OpenCV", "数据科学", ("opencv-python", "opencv-python-headless", "cv2"), "计算机视觉库", "python"),
    T("Pillow", "数据科学", ("pillow", "pil"), "图像处理库", "python"),
    T("PySpark", "数据科学", ("pyspark",), "Spark 的 Python 接口", "python"),
    T("Polars", "数据科学", ("polars",), "Rust 内核的高速 DataFrame", "python"),
    T("Dask", "数据科学", ("dask",), "并行计算框架", "python"),

    # ---------------------------------------------------------------- 监控与观测
    T("Prometheus", "监控与观测", ("prometheus", "prometheus-client", "prom-client"), "指标采集与监控", "any"),
    T("Grafana", "监控与观测", ("grafana",), "监控可视化面板", "any"),
    T("Sentry", "监控与观测", ("sentry", "sentry-sdk", "@sentry/node", "@sentry/react"), "错误追踪平台", "any"),
    T("OpenTelemetry", "监控与观测", ("opentelemetry", "opentelemetry-api", "opentelemetry-sdk", "@opentelemetry/api"), "可观测性标准", "any"),
    T("Jaeger", "监控与观测", ("jaeger", "jaeger-client"), "分布式链路追踪", "any"),

    # ---------------------------------------------------------------- 其他常见
    T("Requests", "其他依赖", ("requests",), "Python HTTP 客户端", "python"),
    T("HTTPX", "其他依赖", ("httpx",), "支持异步的 Python HTTP 客户端", "python"),
    T("BeautifulSoup", "其他依赖", ("beautifulsoup4", "bs4"), "HTML 解析库", "python"),
    T("Scrapy", "其他依赖", ("scrapy",), "Python 爬虫框架", "python"),
    T("PyYAML", "其他依赖", ("pyyaml", "yaml"), "YAML 解析库", "python"),
    T("Click", "其他依赖", ("click",), "Python 命令行框架", "python"),
    T("Typer", "其他依赖", ("typer",), "基于类型提示的 CLI 框架", "python"),
    T("Rich", "其他依赖", ("rich",), "终端富文本输出", "python"),
    T("Loguru", "其他依赖", ("loguru",), "更好用的 Python 日志库", "python"),
    T("Lombok", "其他依赖", ("lombok", "org.projectlombok"), "Java 注解处理器，减少样板代码", "java"),
    T("OpenSSL", "其他依赖", ("openssl", "libssl"), "加密与 TLS 基础库", "any"),
    T("cURL", "其他依赖", ("curl", "libcurl"), "C/C++ 的 HTTP 客户端库", "any"),
]


# ============================================================================
# 索引与查询
# ============================================================================
def normalize_name(raw: str) -> str:
    """把各种写法统一：小写、去空格、下划线变短横线。"""
    return raw.strip().lower().replace("_", "-")


# 这些名字过于宽泛，只允许"精确匹配"，不允许"前缀匹配"。
# 例如 python-oxmsg 不应该被当成 Python 语言，node-fetch 不应该被当成 Node.js。
NO_PREFIX_ALIASES = {
    "python",
    "python3",
    "java",
    "javascript",
    "typescript",
    "node",
    "nodejs",
    "node.js",
    "go",
    "golang",
    "rust",
    "php",
    "ruby",
    "kotlin",
    "swift",
    "scala",
    "dart",
    "shell",
    "bash",
    "make",
    "uv",
    "rq",
    "k6",
    "nats",
    "rocket",
    "relay",
    "hapi",
}


def _build_indexes() -> tuple[dict[str, TechSpec], list[tuple[str, TechSpec]]]:
    exact: dict[str, TechSpec] = {}
    for spec in CATALOG:
        for alias in (spec.name, *spec.aliases):
            key = normalize_name(alias)
            if key and key not in exact:
                exact[key] = spec
    # 前缀匹配用的列表：别名越长越优先，避免 "go" 抢走 "google.golang.org/grpc"。
    prefixes = sorted(
        (
            (alias, spec)
            for alias, spec in exact.items()
            if len(alias) >= 4 and alias not in NO_PREFIX_ALIASES
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    return exact, prefixes


_EXACT, _PREFIXES = _build_indexes()


def lookup(raw: str) -> TechSpec | None:
    """查词典：先精确匹配，再前缀匹配。查不到返回 None。"""
    key = normalize_name(raw)
    if not key:
        return None
    spec = _EXACT.get(key)
    if spec is not None:
        return spec
    for alias, candidate in _PREFIXES:
        if key.startswith(alias + "-") or key.startswith(alias + "/") or key.startswith(alias + ".") or key.startswith(alias + ":"):
            return candidate
    return None


def guess_generic_category(name: str) -> str:
    """词典里没有的名字，用关键词猜一个分类（只是为了让页面好看一点）。"""
    lowered = name.lower()
    if any(word in lowered for word in ("test", "mock", "assert", "lint", "format", "coverage")):
        return "测试与质量"
    if any(word in lowered for word in ("webpack", "vite", "rollup", "babel", "build", "gradle", "maven", "cargo")):
        return "构建与工具链"
    if any(word in lowered for word in ("sql", "jdbc", "mongo", "redis", "mysql", "postgres", "orm", "database")):
        return "数据库"
    if any(word in lowered for word in ("kafka", "rabbit", "amqp", "queue", "mq")):
        return "缓存与消息"
    if any(word in lowered for word in ("sentry", "prometheus", "grafana", "otel", "telemetry", "jaeger")):
        return "监控与观测"
    if any(word in lowered for word in ("docker", "k8s", "kubernetes", "nginx", "terraform")):
        return "基础设施与运维"
    if any(word in lowered for word in ("react", "vue", "angular", "svelte", "css", "ui")):
        return "前端框架"
    if any(word in lowered for word in ("django", "flask", "fastapi", "spring", "express", "koa", "nest")):
        return "后端框架"
    return "其他依赖"


def should_skip_dependency(name: str) -> bool:
    """判断一个依赖名是不是"噪音"，不值得展示。"""
    lowered = name.strip().lower()
    if not lowered:
        return True
    if lowered in NOISE_PACKAGES:
        return True
    if lowered.startswith("@types/"):
        return True
    if lowered.startswith("eslint-") or lowered.startswith("prettier-plugin-"):
        return True
    if lowered in {"-e", ".", ".."}:
        return True
    if lowered.startswith("git+") or lowered.startswith("http://") or lowered.startswith("https://"):
        return True
    return False
