import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import backend
repo_root = Path(__file__).parent
sys.path.append(str(repo_root))
sys.path.append(str(repo_root / "packages" / "aethergrid_core" / "src"))
sys.path.append(str(repo_root / "packages" / "theory" / "src"))
sys.path.append(str(repo_root / "packages" / "evaluation" / "src"))
sys.path.append(str(repo_root / "packages" / "sovereign_watchdog" / "src"))
sys.path.append(str(repo_root / "packages" / "models" / "src"))

from backend.app.main import app

with open("c:\\Users\\aniru\\Downloads\\AetherGrid-Sovereign-main\\openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)
