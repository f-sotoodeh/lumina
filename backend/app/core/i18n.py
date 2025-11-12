import yaml
from pathlib import Path
from typing import Dict

class Translator:
    _instance = None
    _translations: Dict[str, Dict] = {}

    def __init__(self):
        if not self._translations:
            self._load_translations()

    def _load_translations(self):
        locale_path = Path(__file__).parent.parent / "locales"
        for file in locale_path.glob("*.yaml"):
            lang = file.stem
            with open(file, "r", encoding="utf-8") as f:
                self._translations[lang] = yaml.safe_load(f)

    @classmethod
    def get(cls, lang: str = "en"):
        if cls._instance is None:
            cls._instance = cls()
        return cls._translations.get(lang, cls._translations["en"])
