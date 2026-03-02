import yaml
import os

class GameConfig:
    def __init__(self, **kwargs):
        # Set default values matching game_config.yaml structure
        defaults = {
            "mode": "human",
            "language": "en",
            "seed": -1,
            "character": "Ironclad",
            "ascension": 0,
            "select_overflow": "truncate",
            "auto_select": False,  # Auto select for all modes (human, ai, debug)
            "human": {
                "show_menu_option": True,
                "ai_coach": True,
            },
            "ai": {
                "api_key": os.environ.get("OPENAI_API_KEY", ""),
                "api_base": "https://api.openai.com/v1",
                "model": "gpt-4o",
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 2048,
                "timeout": 60,
            },
            "debug": {
                "print": False,
                "select_type": "random",
                "god_mode": False,
            },
            "gameplay": {
                "enable_combat_challenges": True,
            },
        }

        # Deep merge for nested configs
        for key, value in kwargs.items():
            if key in defaults and isinstance(defaults[key], dict) and isinstance(value, dict):
                defaults[key] = {**defaults[key], **value}
            else:
                defaults[key] = value

        # Set attributes explicitly
        self.mode = defaults["mode"]
        self.language = defaults["language"]
        self.seed = defaults["seed"]
        self.character = defaults["character"]
        self.ascension = defaults["ascension"]
        self.select_overflow = defaults["select_overflow"]
        self.auto_select = defaults["auto_select"]
        self.human = defaults["human"]
        self.ai = defaults["ai"]
        self.debug = defaults["debug"]
        self.gameplay = defaults["gameplay"]

    def get(self, key, default=None):
        """Dict-like access for compatibility with config.get usage.

        Supports nested access via dot notation: get("human.auto_select")
        """
        if "." in key:
            parts = key.split(".", 1)
            first = getattr(self, parts[0], None)
            if first is None:
                return default
            if isinstance(first, dict):
                return first.get(parts[1], default)
            return getattr(first, parts[1], default)
        return getattr(self, key, default)

    @staticmethod
    def load(config_path):
        import shutil
        template_path = os.path.join(os.path.dirname(config_path), "game_config_template.yaml")
        
        if not os.path.exists(config_path):
            if os.path.exists(template_path):
                print(f"Config file not found. Creating {config_path} from template...")
                shutil.copy2(template_path, config_path)
            else:
                print("Warning: Neither config file nor template found. Using defaults.")
                return GameConfig()

        try:
            with open(config_path, "r", encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data is None:
                    return GameConfig()
                return GameConfig(**data)
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return GameConfig()
