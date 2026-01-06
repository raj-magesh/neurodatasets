import mne
import numpy as np
import numpy.typing as npt
import pandas as pd

from neurodatasets._utilities import NEURODATASETS_HOME
from neurodatasets.files import download_from_url, untar

from ._utilities import IDENTIFIER

URL = "https://plus.figshare.com/ndownloader/files/36827316"

BIDS_HOME = NEURODATASETS_HOME / IDENTIFIER / "THINGS-MEG"

N_SUBJECTS = 4
N_SESSIONS = 12
N_RUNS_PER_SESSION = 10

SAMPLING_FREQUENCY_IN_HZ = 1_200
STIMULUS_DURATION_IN_S = 0.5

OPTICAL_SENSOR_CHANNEL = "UADC016-2104"
TRIGGER_CHANNEL = "UPPT001"
TRIGGER_VALUE = 64


def download_dataset() -> None:
    cache_path = NEURODATASETS_HOME / IDENTIFIER

    filepath = cache_path / "downloads" / "THINGS-MEG.tar.gz"

    download_from_url(URL, filepath=filepath)
    untar(filepath, extract_dir=cache_path, remove_tar=True)

    for path in (cache_path / "THINGS-MEG").rglob("._*"):
        path.unlink()

    for path in (cache_path / "THINGS-MEG").rglob("*DS_Store*"):
        path.unlink()


def load_raw_ctf(*, subject: int, session: int, run: int) -> mne.io.Raw:
    directory = (
        BIDS_HOME
        / f"sub-BIGMEG{1 + subject}"
        / f"ses-{1 + session:02}"
        / "meg"
        / f"sub-BIGMEG{1 + subject}_ses-{1 + session:02}_task-main_run-{1 + run:02}_meg.ds"
    )
    return mne.io.read_raw_ctf(directory)


def extract_onsets(
    ctf: mne.io.Raw,
    *,
    optical_sensor_threshold: float = 1,
    max_delta: int = 20,
) -> npt.NDArray[np.integer]:
    triggers = ctf.copy().pick(TRIGGER_CHANNEL).get_data()[0]
    optical_sensor = ctf.copy().pick(OPTICAL_SENSOR_CHANNEL).get_data()[0]

    onsets_trigger = (
        1 + np.nonzero(np.diff((triggers == TRIGGER_VALUE).astype(int)) > 0)[0]
    )
    onsets_optical = (
        1
        + np.nonzero(
            np.diff((optical_sensor >= optical_sensor_threshold).astype(int)) > 0
        )[0]
    )

    allowed_onsets = np.concatenate([
        onsets_trigger + delta for delta in range(max_delta)
    ])
    return onsets_optical[np.isin(onsets_optical, allowed_onsets)]


def extract_epochs(
    *,
    subject: int,
    session: int,
    run: int,
    t_min: float = -0.1,
    t_max: float = 1.3,
) -> mne.Epochs:
    ctf = load_raw_ctf(subject=subject, session=session, run=run)

    onsets = extract_onsets(ctf)

    filepath = (
        BIDS_HOME
        / f"sub-BIGMEG{1 + subject}"
        / f"ses-{1 + session:02}"
        / "meg"
        / f"sub-BIGMEG{1 + subject}_ses-{1 + session:02}_task-main_run-{1 + run:02}_events.tsv"
    )

    metadata = (
        pd
        .read_csv(filepath, sep="\t")
        .assign(
            stimulus=lambda x: [
                filepath.split("/")[-1][:-4] for filepath in x["file_path"]
            ],
            trial_type=lambda x: x["trial_type"].replace({"exp": "experiment"}),
        )
        .assign(
            category=lambda x: [
                "_".join(stimulus.split("_")[:-1]) for stimulus in x["stimulus"]
            ]
        )
        .loc[:, ["stimulus", "category", "trial_type", "RT"]]
    )

    annotations = mne.Annotations(
        onset=onsets / SAMPLING_FREQUENCY_IN_HZ,
        duration=STIMULUS_DURATION_IN_S,
        description=metadata["stimulus"].tolist(),
    )

    return mne.Epochs(
        ctf.set_annotations(annotations),
        tmin=t_min,
        tmax=t_max,
        metadata=metadata,
    )
