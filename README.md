<div align="center">

# 🎮 Slay the Model

**一个结构清晰的《杀戮尖塔》游戏核心框架**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/zhujiayu999/slay-the-model.svg)](https://github.com/zhujiayu999/slay-the-model/stargazers)

**[English](README_EN.md) | 中文**

</div>

---

### 📖 项目简介

**Slay the Model** 是一个基于 Python 的《杀戮尖塔》(Slay the Spire) 核心游戏框架。

与原版反编译代码不同，本项目从软件工程角度重新设计，实现了**表现层与逻辑层的完全分离**，提供了一个结构清晰、易于扩展、方便研究的游戏系统内核。

#### 🎯 项目动机

《杀戮尖塔》的玩法设计非常优秀，但从软件工程角度分析，原版代码存在一些问题：

- 表现层与逻辑层耦合较重
- 基类复杂度过高
- 不方便做大规模并行实验

因此，本项目在不涉及图形系统的前提下，重写了一个结构清晰、逻辑独立的核心框架。

#### ✨ 核心特性

- 🏗️ **清晰的架构设计**：表现层与逻辑层完全分离，代码结构模块化
- 🎮 **完整游戏机制**：实现卡牌战斗、遗物系统、药水系统、事件系统等
- 🤖 **AI 接口支持**：支持接入大语言模型自动进行游戏决策
- 🔬 **Debug 模式**：支持随机测试、上帝模式等调试功能
- ⚡ **并行运行**：无图形依赖，可并行运行多个游戏实例
- 🌍 **本地化支持**：支持中英文切换
- ⚙️ **高度可配置**：通过 YAML 配置文件自定义游戏参数

#### 🎓 适用场景

- **游戏开发者**：参考卡牌游戏的核心架构设计
- **研究人员**：进行游戏 AI、强化学习相关研究
- **内容创作者**：快速测试和验证游戏机制

---

### 🏗️ 架构设计

#### 核心设计理念

1. **战斗状态机**：战斗开始 → (玩家回合 → 敌人回合) 循环
2. **Action 执行队列**：非即时游戏的经典框架，一个动作触发另一个动作
3. **本地化系统**：游戏编程中只使用 key，由本地化系统查找对应字符串
4. **精简基类设计**：如卡牌基类仅约 500 行（原版反编译代码数千行）

#### 项目结构

```
slay-the-model/
├── actions/        # 动作系统（Action 队列核心）
├── cards/          # 卡牌系统
├── enemies/        # 敌人定义（按章节分类）
├── relics/         # 遗物系统
├── potions/        # 药水系统
├── powers/         # 能力/buff/debuff 系统
├── events/         # 事件系统
├── engine/         # 游戏引擎核心
│   ├── combat.py       # 战斗引擎
│   ├── combat_state.py # 战斗状态管理
│   ├── game_flow.py    # 游戏流程控制
│   └── game_state.py   # 全局游戏状态
├── player/         # 玩家系统
├── map/            # 地图生成与管理
├── rooms/          # 房间类型
├── tui/            # 终端用户界面（可选）
├── ai/             # AI 接口
├── localization/   # 本地化文件
└── config/         # 配置文件
```

---

### 🔧 环境配置

#### 系统要求

- Python 3.8 或更高版本
- Windows / macOS / Linux

#### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/zhujiayu999/slay-the-model.git
cd slay-the-model
```

2. **创建虚拟环境（推荐）**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

---

### ⚙️ 配置说明

配置文件位于 `config/game_config.yaml`。首次使用时，请复制模板：

```bash
cp config/game_config_template.yaml config/game_config.yaml
```

#### 游戏模式

| 模式 | 说明 |
|------|------|
| `human` | 人类控制，通过 TUI 界面进行游戏 |
| `ai` | AI 控制，接入 LLM 自动决策 |
| `debug` | 调试模式，支持随机输入测试 |

#### 配置项说明

| 配置项 | 说明 | 可选值 |
|--------|------|--------|
| `mode` | 游戏模式 | `human` / `ai` / `debug` |
| `language` | 界面语言 | `zh` (中文) / `en` (英文) |
| `seed` | 随机种子 | 任意整数 |
| `character` | 角色 | `Ironclad` (目前仅支持铁甲战士) |
| `ascension` | 进阶等级 | `0-20` (0表示无进阶) |

#### AI 模式配置

```yaml
ai:
  api_key: YOUR_API_KEY        # API 密钥
  api_base: YOUR_MODEL_API_BASE # API 地址
  model: YOUR_MODEL             # 模型名称
  stream: True                  # 是否流式输出
  temperature: 0.7              # 温度参数
  max_tokens: 8192             # 最大 token 数
  timeout: 60                   # 超时时间（秒）
```

#### 调试模式配置

```yaml
debug:
  print: False          # 是否打印调试信息
  select_type: random   # 选择方式: random / first
  god_mode: False       # 上帝模式（敌人1血）
```

---

### 🚀 运行项目

#### TUI 模式（默认）

```bash
python __main__.py
```

#### CLI 模式（无界面）

```bash
python __main__.py --no-tui
```

---

### 📦 发布与打包

#### 运行发布版本 (Release)

1. 在 [Releases](https://github.com/zhujiayu999/slay-the-model/releases) 页面下载最新版本的压缩包。
2. 解压后直接运行 `slay-the-model.exe` 即可开始游戏。
3. **注意**：首次运行会自动在同级目录生成 `config/game_config.yaml`（如果是从源码打包）。发布版固化了资源，但仍会读取外部配置。

#### 开发者打包步骤

如果你想自行打包成可执行文件：

1. 安装 PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. 使用提供的 spec 文件进行打包:
   ```bash
   pyinstaller slay-the-model.spec
   ```
3. 打包完成后，可执行文件位于 `dist/slay-the-model.exe`。

---

### 🔬 研究用途

#### 并行实验

由于无图形依赖，框架支持并行运行多个游戏实例，适合：

- 大规模 AI 对战评估
- 强化学习训练数据采集
- 游戏平衡性测试

#### 接入强化学习

框架提供了清晰的 state/action 接口，易于接入强化学习算法：

- 状态空间：玩家 HP、牌组、遗物、敌人信息等
- 动作空间：出牌、使用药水、结束回合等
- 奖励信号：战斗胜利、伤害输出、生存回合等

---

### 📋 开发路线

#### 🐛 Bug 修复 (High Priority)

- [x] 涅奥的祝福没有效果修复 (Fixed in df7442f)
- [x] 变异之力（Mutagenic Strength）在第一回合结束未正确失去力量修复 (Fixed in 7a04ae6)
- [ ] 本地化显示问题修复
- [ ] 错误处理优化
- [ ] 卡牌效果校对与修复
- [ ] 遗物效果校对与修复
- [ ] 药水效果校对与修复
- [ ] 能力（Power）效果校对与修复
- [ ] 敌人行为/意图校对与修复

#### 🎮 游戏功能补充 (Medium Priority)

- [ ] 不同进阶等级下的游戏机制变化
- [ ] 三把钥匙获取系统
- [ ] 是否强制进入 Act 4 的配置

#### 🎮 游戏功能补充 (Low Priority)

- [ ] 更多角色支持（Silent、Defect、Watcher）

#### ✨ Feature (High Priority)

- [ ] 支持本地部署 LLM
- [ ] 完善文档
- [ ] 强化学习接口

#### ✨ Feature (Medium Priority)

- [ ] 自动对战评估环境
- [ ] 添加更多测试用例

---

### 🛠️ 开发工具

本项目使用 Vibe Coding 方式开发，主要工具：

- **IDE**: VS Code + Opencode
- **模型**: GLM-5（架构设计）+ Codex-5.3（代码实现）

#### 开发经验

> 💡 **核心原则**：人类负责结构约束，模型负责填充实现

1. **架构优先**：先定义状态机、Action 队列、本地化系统、基类设计
2. **外部知识拉取**：通过 MCP/Web Skills 拉取卡牌效果、怪物数值等资料
3. **迭代测试**：使用自动化测试进行迭代验证

---

### 🤝 贡献指南

欢迎提交 Issue 和 PR！特别是：

- 🐛 Bug 报告
- 📝 文档改进
- 🎮 游戏机制完善
- 🤖 AI/RL 接口改进

---

### 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

### 🙏 致谢

- 《杀戮尖塔》by MegaCrit
- 所有贡献者

---

<div align="center">

**Made with ❤️ by zhujiayu999**

</div>