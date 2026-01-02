import os
from pathlib import Path

from xdg_base_dirs import xdg_data_home

NEURODATASETS_HOME = Path(
    os.getenv(
        "NEURODATASETS_HOME",
        str(xdg_data_home() / ".cache" / "neurodatasets"),
    ),
)
