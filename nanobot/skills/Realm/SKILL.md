---
name: Realm
description: Realm 项目开发助手 / Realm Project Development Assistant. Intelligently routes development tasks to Claude Code sessions for project analysis, optimization, code generation, and more. Use when you need to analyze projects, optimize code, generate documentation, or invoke project interfaces.
metadata: {"nanobot":{"emoji":"🚀","requires":{"bins":["python3"]}}}
---

# Realm Skill - NanoBot 项目开发助手

Realm Skill 是一个为 NanoBot 设计的专业项目开发助手。它能够自动识别开发需求，将任务智能分发到对应的 Claude Code session，并返回执行结果。

## 概述

- 🚀 **自动识别开发需求** - 从自然语言中提取项目名称和任务类型
- 📊 **智能任务分发** - 将任务自动分发到对应的 Claude Code session
- 💻 **远程开发支持** - 支持通过飞书/钉钉进行远程开发
- ⏱️ **进度跟踪** - 监控任务执行进度并返回结果

## 支持的项目

| 项目名 | 别名 | 类型 |
|--------|------|------|
| Athena | athena | TypeScript |
| Personal_Resume-main | 简历, resume, personal | TypeScript |
| guameow_flutter | guameow, flutter | Flutter |
| prism-resume-forge | prism, pdf | TypeScript |
| Realm | realm | TypeScript |
| information_crawler | 爬虫, crawler | Python |

## 支持的任务类型

- **分析** - 分析项目结构、能力、架构
- **优化** - 优化代码、性能、UI/UX
- **生成** - 生成文档、代码、配置
- **调用** - 调用项目接口、获取数据
- **创建** - 创建新的项目 session
- **修复** - 修复 bug、问题
- **改进** - 改进功能、流程

## 使用方法

### 基本指令

在飞书中发送以下指令：

```
分析 Athena 项目的整体架构
优化 Personal_Resume-main 项目的项目介绍模块的 UI 和 UX
为 guameow_flutter 项目生成技术文档
调用 Athena 的接口，告诉我今天有什么新的事儿
创建 information_crawler session，分析爬虫金链路流程
```

### 列出所有项目

```
列出所有项目
```

## 工作流程

```
用户在飞书发送指令
    ↓
NanoBot 接收消息
    ↓
检测是否是开发类需求
    ↓
调用 Realm Skill
    ↓
Skill 解析项目和任务类型
    ↓
调用 Realm API 分发任务
    ↓
Realm 路由到对应 session
    ↓
Claude Code 执行任务
    ↓
结果回调给 NanoBot
    ↓
NanoBot 格式化结果
    ↓
飞书显示结果
```

## 示例

### 示例 1: 分析项目结构

**输入：**
```
分析 Athena 项目的整体架构
```

**输出：**
```
✅ 任务已成功分发！

📋 项目: Athena
🎯 任务类型: analyze
📝 描述: 分析 Athena 项目的整体架构
🔗 Task Group ID: abc123

⏳ 正在处理中...
💬 结果将通过飞书回复给你
```

### 示例 2: 优化 UI/UX

**输入：**
```
优化 Personal_Resume-main 项目的项目介绍模块的 UI 和 UX
```

**输出：**
```
✅ 任务已成功分发！

📋 项目: Personal_Resume-main
🎯 任务类型: optimize
📝 描述: 优化 Personal_Resume-main 项目的项目介绍模块的 UI 和 UX
🔗 Task Group ID: def456

⏳ 正在处理中...
💬 结果将通过飞书回复给你
```

## 故障排查

### 问题 1: "我没有识别到具体的项目"

**原因：** 消息中没有明确的项目名称

**解决：** 在指令中明确指定项目名称，例如：
```
分析 Athena 项目的结构
```

### 问题 2: "任务分发失败"

**原因：** Realm 服务器未运行或无法连接

**解决：**
1. 确保 Realm 服务器运行：`npm run server`
2. 检查 Realm 地址配置是否正确
3. 查看 NanoBot 日志

### 问题 3: 没有收到结果

**原因：** 任务仍在执行或回调失败

**解决：**
1. 等待更长时间（任务可能需要几分钟）
2. 检查 Realm 日志
3. 验证回调 URL 配置
