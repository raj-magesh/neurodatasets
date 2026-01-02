from pathlib import Path

from neurodatasets._utilities import NEURODATASETS_HOME
from neurodatasets.files import download_from_url, untar

IDENTIFIER = "hebart2023.things-data"
CACHE_PATH = NEURODATASETS_HOME / IDENTIFIER / "meg"
N_SUBJECTS = 4
N_SESSIONS = 12

URLS = {
    "preprocessed": "https://plus.figshare.com/ndownloader/files/39472855",
    "raw": "https://plus.figshare.com/ndownloader/files/36827316",
}


def download_dataset(*, preprocessed: bool = True) -> Path:
    url = URLS["preprocessed" if preprocessed else "raw"]
    filepath = download_from_url(
        url,
        filepath=CACHE_PATH / "downloads" / f"preprocessed={preprocessed}.tar.gz",
    )
    filepath = untar(
        filepath,
        extract_dir=CACHE_PATH / "preprocessed",
        remove_tar=False,
    )
    return filepath
