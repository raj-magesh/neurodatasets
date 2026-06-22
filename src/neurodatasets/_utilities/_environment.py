import os
from pathlib import Path

if neurodatasets_home := os.getenv("NEURODATASETS_HOME"):
    NEURODATASETS_HOME = Path(neurodatasets_home)
elif xdg_data_home := os.getenv("XDG_DATA_HOME"):
    NEURODATASETS_HOME = Path(xdg_data_home) / "neurodatasets"
else:
    NEURODATASETS_HOME = Path.home() / ".local" / "share" / "neurodatasets"
