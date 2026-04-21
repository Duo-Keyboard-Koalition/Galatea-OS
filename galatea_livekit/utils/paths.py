import os
from pathlib import Path

class PathManager:
    # GALATEA_MODE can be 'prod' or 'dev'
    MODE = os.getenv("GALATEA_MODE", "dev")
    
    @classmethod
    def get_root(cls) -> Path:
        # Priority: 
        # 1. GALATEA_ROOT environment variable (Folder of choosing in dev)
        # 2. Prod mode -> ~/.galatea
        # 3. Dev mode fallback -> .galatea in the project root
        
        env_root = os.getenv("GALATEA_ROOT")
        if env_root:
            root = Path(env_root)
        elif cls.MODE == "prod":
            root = Path.home() / ".galatea"
        else:
            # Fallback to a .galatea folder in the current project root
            root = Path(__file__).resolve().parent.parent.parent / ".galatea"
        
        root.mkdir(parents=True, exist_ok=True)
        return root

    @classmethod
    def get_config_path(cls) -> Path:
        return cls.get_root() / "config.json"

    @classmethod
    def get_soul_path(cls) -> Path:
        return cls.get_root() / "SOUL.md"

    @classmethod
    def get_skills_path(cls) -> Path:
        return cls.get_root() / "SKILLS.md"

    @classmethod
    def get_data_dir(cls) -> Path:
        d = cls.get_root() / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @classmethod
    def get_db_path(cls, db_name: str) -> str:
        return str(cls.get_data_dir() / f"{db_name}.db")
