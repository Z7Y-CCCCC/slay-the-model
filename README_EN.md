<div align="center">

# 🎮 Slay the Model

**A Well-Structured Slay the Spire Game Core Framework**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/zhujiayu999/slay-the-model.svg)](https://github.com/zhujiayu999/slay-the-model/stargazers)

**English | [中文](README.md)**

</div>

---

### 📖 Introduction

**Slay the Model** is a Python-based core game framework for *Slay the Spire*.

Unlike the decompiled original code, this project is redesigned from a software engineering perspective, achieving **complete separation of presentation and logic layers**, providing a clean, extensible, and research-friendly game system kernel.

#### 🎯 Motivation

Slay the Spire has excellent gameplay design, but from a software engineering perspective, the original code has some issues:

- Heavy coupling between presentation and logic layers
- High complexity in base classes
- Difficult to conduct large-scale parallel experiments

Therefore, this project rewrites a clean, logically independent core framework without involving the graphics system.

#### ✨ Key Features

- 🏗️ **Clean Architecture**: Complete separation of presentation and logic layers, modular code structure
- 🎮 **Complete Game Mechanics**: Card combat, relic system, potion system, event system, etc.
- 🤖 **AI Interface Support**: Support for LLM-based automatic game decision-making
- 🔬 **Debug Mode**: Support for random testing, god mode, and other debugging features
- ⚡ **Parallel Execution**: No graphics dependency, can run multiple game instances in parallel
- 🌍 **Localization**: Support for Chinese and English
- ⚙️ **Highly Configurable**: Customize game parameters via YAML config files

#### 🎓 Use Cases

- **Game Developers**: Reference for core architecture design of card games
- **Researchers**: Conduct game AI and reinforcement learning research
- **Content Creators**: Quickly test and verify game mechanics

---

### 🏗️ Architecture Design

#### Core Design Principles

1. **Combat State Machine**: Combat start → (Player turn → Enemy turn) loop
2. **Action Execution Queue**: Classic framework for non-realtime games, one action triggers another
3. **Localization System**: Only use keys in game code, localization system looks up corresponding strings
4. **Simplified Base Class Design**: Card base class is only ~500 lines (vs thousands in decompiled code)

#### Project Structure

```
slay-the-model/
├── actions/        # Action system (Action queue core)
├── cards/          # Card system
├── enemies/        # Enemy definitions (by act)
├── relics/         # Relic system
├── potions/        # Potion system
├── powers/         # Power/buff/debuff system
├── events/         # Event system
├── engine/         # Game engine core
│   ├── combat.py       # Combat engine
│   ├── combat_state.py # Combat state management
│   ├── game_flow.py    # Game flow control
│   └── game_state.py   # Global game state
├── player/         # Player system
├── map/            # Map generation and management
├── rooms/          # Room types
├── tui/            # Terminal user interface (optional)
├── ai/             # AI interface
├── localization/   # Localization files
└── config/         # Configuration files
```

---

### 🔧 Environment Setup

#### Requirements

- Python 3.8 or higher
- Windows / macOS / Linux

#### Installation

1. **Clone the repository**
```bash
git clone https://github.com/zhujiayu999/slay-the-model.git
cd slay-the-model
```

2. **Create virtual environment (recommended)**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

---

### ⚙️ Configuration

The configuration file is located at `config/game_config.yaml`. For first-time use, copy the template:

```bash
cp config/game_config_template.yaml config/game_config.yaml
```

#### Game Modes

| Mode | Description |
|------|-------------|
| `human` | Human control via TUI interface |
| `ai` | AI control with LLM automatic decision-making |
| `debug` | Debug mode with random input testing |

#### Configuration Options

| Option | Description | Values |
|--------|-------------|--------|
| `mode` | Game mode | `human` / `ai` / `debug` |
| `language` | Interface language | `zh` (Chinese) / `en` (English) |
| `seed` | Random seed | Any integer |
| `character` | Character | `Ironclad` (currently only Ironclad supported) |
| `ascension` | Ascension level | `0-20` (0 means no ascension) |

#### AI Mode Configuration

```yaml
ai:
  api_key: YOUR_API_KEY        # API key
  api_base: YOUR_MODEL_API_BASE # API endpoint
  model: YOUR_MODEL             # Model name
  stream: True                  # Stream output
  temperature: 0.7              # Temperature
  max_tokens: 8192             # Max tokens
  timeout: 60                   # Timeout (seconds)
```

#### Debug Mode Configuration

```yaml
debug:
  print: False          # Print debug info
  select_type: random   # Selection type: random / first
  god_mode: False       # God mode (enemies have 1 HP)
```

---

### 🚀 Running the Project

#### TUI Mode (Default)

```bash
python __main__.py
```

#### CLI Mode (No UI)

```bash
python __main__.py --no-tui
```

---

### 📦 Release & Packaging

#### Running the Release Version

1. Download the latest release from the [Releases](https://github.com/zhujiayu999/slay-the-model/releases) page.
2. Extract the files and run `slay-the-model.exe` directly.
3. **Note**: On the first run, the app will look for `config/game_config.yaml`. The executable bundles internal assets but allows external configuration.

#### Developer Packaging Steps

To build the executable yourself:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build using the provided spec file:
   ```bash
   pyinstaller slay-the-model.spec
   ```
3. The resulting executable will be in `dist/slay-the-model.exe`.

---

### 🔬 Research Applications

#### Parallel Experiments

Without graphics dependencies, the framework supports running multiple game instances in parallel, suitable for:

- Large-scale AI battle evaluation
- Reinforcement learning training data collection
- Game balance testing

#### Reinforcement Learning Integration

The framework provides clear state/action interfaces, easy to integrate with RL algorithms:

- State space: Player HP, deck, relics, enemy info, etc.
- Action space: Play cards, use potions, end turn, etc.
- Reward signals: Combat victory, damage output, survival rounds, etc.

---

### 📋 Roadmap

#### 🐛 Bug Fixes (High Priority)

- [x] Fixed Neow's Blessing not taking effect (Fixed in df7442f)
- [x] Fixed Mutagenic Strength not properly losing strength at the end of the 1st turn (Fixed in 7a04ae6)
- [ ] Fix localization display issues
- [ ] Improve error handling
- [ ] Verify and fix card effects
- [ ] Verify and fix relic effects
- [ ] Verify and fix potion effects
- [ ] Verify and fix power effects
- [ ] Verify and fix enemy behaviors/intentions

#### 🎮 Game Features (Medium Priority)

- [ ] Game mechanics changes at different ascension levels
- [ ] Three keys acquisition system
- [ ] Configuration for forced Act 4 entry

#### 🎮 Game Features (Low Priority)

- [ ] Support for more characters (Silent, Defect, Watcher)

#### ✨ Features (High Priority)

- [ ] Support for local LLM deployment
- [ ] Improve documentation
- [ ] Reinforcement learning interface

#### ✨ Features (Medium Priority)

- [ ] Automated battle evaluation environment
- [ ] Add more test cases

---

### 🛠️ Development Tools

This project is developed using Vibe Coding, with main tools:

- **IDE**: VS Code + Opencode
- **Models**: GLM-5 (architecture design) + Codex-5.3 (code implementation)

#### Development Experience

> 💡 **Core Principle**: Humans handle structural constraints, models handle implementation

1. **Architecture First**: Define state machines, Action queues, localization systems, base class designs first
2. **External Knowledge Fetching**: Pull card effects, monster stats, and other data via MCP/Web Skills
3. **Iterative Testing**: Use automated testing for iterative verification

---

### 🤝 Contributing

Issues and PRs are welcome! Especially:

- 🐛 Bug reports
- 📝 Documentation improvements
- 🎮 Game mechanics enhancements
- 🤖 AI/RL interface improvements

---

### 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

### 🙏 Acknowledgments

- *Slay the Spire* by MegaCrit
- All contributors

---

<div align="center">

**Made with ❤️ by zhujiayu999**

</div>