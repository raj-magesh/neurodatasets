import os
from pathlib import Path

NEURODATASETS_HOME = Path(
    os.getenv("NEURODATASETS_HOME", str(Path.home() / ".cache" / "neurodatasets")),
)
