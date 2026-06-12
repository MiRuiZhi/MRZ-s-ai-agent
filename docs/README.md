# 文档导航

这里是 MRZ's AI Agent 的详细文档入口。顶层 [README](../README.md) 负责快速理解项目，这个目录负责展开架构、开发、部署和项目表达。

## 推荐阅读顺序

1. [项目入口](../README.md)：先看模块、能力和快速开始。
2. [仓库结构地图](architecture/repository-map.md)：知道每个目录该看什么。
3. [架构速览](architecture/overview.md)：理解 agent-api、tool-runtime、cpp-worker、ui、deploy 的关系。
4. [使用手册](development/usage.md)：本地启动、接口调用、模型配置和排障。
5. [验证清单](development/testing.md)：改完代码或文档后应该跑哪些检查。
6. [单机 Docker 部署](deployment/single-node-docker.md)：把项目放到本机或服务器跑起来。

## 文档分区

| 分区 | 内容 |
| --- | --- |
| `architecture/` | 架构速览、详细设计、仓库结构地图 |
| `development/` | 使用手册、测试和验证清单 |
| `deployment/` | Docker Compose 与单机部署说明 |
| `project/` | 项目复盘、面试提纲和表达材料 |

## 维护原则

- 顶层 README 只放最短路径：项目是什么、怎么跑、怎么验证、去哪里看更多。
- 详细解释放到 `docs/`，避免根目录越来越散。
- 文档链接要用相对路径，移动文件后必须同步更新引用。
- 文档不进入 Docker 镜像构建上下文，运行镜像只包含服务代码和部署配置。
