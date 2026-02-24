# Nanobot 快速启动指南

本文档说明如何使用启动脚本来运行nanobot并查看实时日志。

## 🚀 快速开始

### 方式1: 完整版启动脚本（推荐）

```bash
cd /Users/sunminghao/Desktop/nanobot
./start_nanobot.sh
```

**功能特点**:
- ✅ 彩色日志输出
- ✅ 自动保存日志到文件
- ✅ 检测是否已有运行中的实例
- ✅ 优雅处理Ctrl+C关闭
- ✅ 自动清理残留进程
- ✅ 显示进程PID和状态

**使用示例**:
```bash
$ ./start_nanobot.sh
========================================
🤖 Nanobot 快速启动脚本
========================================

📝 日志文件: /tmp/nanobot_20260212_162857.log
⚠️  按 Ctrl+C 可安全退出

🚀 正在启动nanobot gateway...

✅ Nanobot已启动 (PID: 12345)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[实时日志输出...]
```

**退出方式**:
按 `Ctrl+C`，脚本会：
1. 捕获终止信号
2. 优雅关闭nanobot进程
3. 清理残留进程
4. 显示日志保存位置
5. 安全退出

---

### 方式2: 简化版启动脚本

```bash
cd /Users/sunminghao/Desktop/nanobot
./start_simple.sh
```

**功能特点**:
- ✅ 最简单，直接运行
- ✅ 实时显示所有输出
- ✅ Ctrl+C自动关闭

**适用场景**: 快速测试或临时使用

---

### 方式3: 直接运行（传统方式）

```bash
nanobot gateway
```

按 `Ctrl+C` 退出。

---

## 📋 日志查看

### 实时日志

使用启动脚本时，日志会自动显示在终端。

### 历史日志

完整版启动脚本会保存日志到 `/tmp/nanobot_*.log`

查看最近的日志：
```bash
ls -lt /tmp/nanobot_*.log | head -5
```

查看特定日志文件：
```bash
cat /tmp/nanobot_20260212_162857.log
```

实时追踪日志文件：
```bash
tail -f /tmp/nanobot_20260212_162857.log
```

---

## 🔧 常见问题

### Q1: 提示"nanobot已经在运行"

**原因**: 已有nanobot进程在后台运行

**解决**:
```bash
# 查看运行中的nanobot进程
ps aux | grep nanobot | grep -v grep

# 终止所有nanobot进程
pkill -f nanobot

# 然后重新启动
./start_nanobot.sh
```

### Q2: 启动失败

**检查步骤**:

1. 确认nanobot已安装：
   ```bash
   which nanobot
   nanobot --version
   ```

2. 查看错误日志：
   ```bash
   cat /tmp/nanobot_*.log | tail -50
   ```

3. 检查端口占用（如果涉及网络）：
   ```bash
   lsof -i :8080  # 根据实际端口修改
   ```

### Q3: Ctrl+C后进程没有完全关闭

**解决**:
```bash
# 强制终止所有nanobot相关进程
pkill -9 -f nanobot

# 或者使用脚本内置的清理逻辑
# start_nanobot.sh 会自动处理这个问题
```

### Q4: 如何在后台运行nanobot？

**不推荐在后台运行**，因为无法实时查看日志和用户交互。

但如果确实需要：
```bash
nohup nanobot gateway > /tmp/nanobot.log 2>&1 &

# 查看日志
tail -f /tmp/nanobot.log

# 停止
pkill -f nanobot
```

---

## 📊 日志内容说明

启动脚本会显示以下类型的日志：

### 1. 系统日志
- 启动信息
- 配置加载
- 连接状态
- 错误信息

### 2. 用户消息
- 来自钉钉/飞书等渠道的用户输入
- 用户ID和频道信息

### 3. Agent消息
- Agent的思考过程
- Tool调用信息
- 响应内容

### 4. Skill执行日志
- Skill加载信息
- 执行状态
- 输出结果

---

## 🎯 推荐使用场景

### 开发调试
使用 **完整版启动脚本** (`start_nanobot.sh`)
- 完整的日志记录
- 便于问题排查
- 保存历史日志

### 日常使用
使用 **简化版启动脚本** (`start_simple.sh`)
- 快速启动
- 简洁输出

### 生产环境
使用 **systemd服务** 或 **Docker容器**
- 自动重启
- 日志轮转
- 资源限制

---

## 📌 提示

1. **定时任务会自动运行**: 启动nanobot后，您之前设置的每日9点舆情监控任务会自动生效

2. **日志级别**: 如果日志太多，可以在nanobot配置中调整日志级别

3. **性能监控**: 使用 `htop` 或 `top` 命令监控nanobot的资源使用

4. **快捷键**:
   - `Ctrl+C`: 优雅退出
   - `Ctrl+Z`: 暂停（不推荐）
   - `Ctrl+\`: 强制退出（不推荐）

---

## 🔗 相关文件

- `start_nanobot.sh` - 完整版启动脚本
- `start_simple.sh` - 简化版启动脚本
- `nanobot/skills/sentiment-monitor/` - 舆情监控skill

---

**祝使用愉快！** 🎉

如有问题，请查看nanobot文档或联系支持。
