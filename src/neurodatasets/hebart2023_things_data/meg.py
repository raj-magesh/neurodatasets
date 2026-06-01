"""Magnetoencephalography (MEG) dataset from the THINGS-data collection.

Citation:
---------

Martin N Hebart, Oliver Contier, Lina Teichmann, Adam H Rockter, Charles Y
Zheng, Alexis Kidder, Anna Corriveau, Maryam Vaziri-Pashkam, Chris I Baker
(2023) THINGS-data, a multimodal collection of large-scale datasets for
investigating object representations in human brain and behavior eLife 12:e82580

https://doi.org/10.7554/eLife.82580
"""

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
FIXATION_PERIOD_IN_S = (0.8, 1.2)

LINE_FREQUENCY_IN_HZ = 60

OPTICAL_SENSOR_CHANNEL = "UADC016-2104"
STIM_CHANNEL = "UPPT001"
STIM_VALUE = 64


def download_dataset() -> None:
    cache_path = NEURODATASETS_HOME / IDENTIFIER

    filepath = cache_path / "downloads" / "THINGS-MEG.tar.gz"

    download_from_url(URL, filepath=filepath)
    untar(filepath, extract_dir=cache_path, remove_tar=True)

    # remove random filesystem detritus
    for path in (cache_path / "THINGS-MEG").rglob("._*"):
        path.unlink()

    for path in (cache_path / "THINGS-MEG").rglob("*DS_Store*"):
        path.unlink()


def load_raw_data(*, subject: int, session: int, run: int) -> mne.io.Raw:
    directory = (
        BIDS_HOME
        / f"sub-BIGMEG{1 + subject}"
        / f"ses-{1 + session:02}"
        / "meg"
        / f"sub-BIGMEG{1 + subject}_ses-{1 + session:02}_task-main_run-{1 + run:02}_meg.ds"
    )
    return mne.io.read_raw_ctf(directory)


def extract_onsets(
    data: mne.io.Raw,
    *,
    optical_sensor_threshold: float = 1,
    max_delta: int = 20,
) -> npt.NDArray[np.integer]:
    triggers = data.copy().pick(STIM_CHANNEL).get_data()[0]
    optical_sensor = data.copy().pick(OPTICAL_SENSOR_CHANNEL).get_data()[0]

    onsets_trigger = (
        1 + np.nonzero(np.diff((triggers == STIM_VALUE).astype(int)) > 0)[0]
    )
    onsets_optical = (
        1
        + np.nonzero(
            np.diff((optical_sensor >= optical_sensor_threshold).astype(int)) > 0
        )[0]
    )

    # In rare situations, the optical trigger is faster than the digital trigger (!?)
    # which is why I allow the delta to be negative.
    # This is weird, but I treat the optical trigger as more accurate in any case,
    # so whatever ¯\_(ツ)_/¯
    allowed_onsets = np.concatenate([
        onsets_trigger + delta for delta in range(-max_delta, max_delta)
    ])
    return onsets_optical[np.isin(onsets_optical, allowed_onsets)]


def load_metadata(
    *,
    subject: int,
    session: int,
    run: int,
) -> pd.DataFrame:
    filepath = (
        BIDS_HOME
        / f"sub-BIGMEG{1 + subject}"
        / f"ses-{1 + session:02}"
        / "meg"
        / f"sub-BIGMEG{1 + subject}_ses-{1 + session:02}_task-main_run-{1 + run:02}_events.tsv"
    )

    return (
        pd
        .read_csv(filepath, sep="\t")
        .assign(
            stimulus=[filepath.split("/")[-1][:-4] for filepath in pd.col("file_path")],
            trial_type=pd.col("trial_type").replace({"exp": "experiment"}),
        )
        .assign(
            category=[
                "_".join(stimulus.split("_")[:-1]) for stimulus in pd.col("stimulus")
            ],
        )
    )


def extract_epochs(
    data: mne.io.Raw,
    *,
    metadata: pd.DataFrame,
    t_min: float = -0.1,
    t_max: float = 1.3,
) -> mne.Epochs:
    onsets = extract_onsets(data)
    annotations = mne.Annotations(
        onset=onsets / SAMPLING_FREQUENCY_IN_HZ,
        duration=STIMULUS_DURATION_IN_S,
        description=[f"stimulus={stimulus}" for stimulus in metadata["stimulus"]],
    )
    return mne.Epochs(
        data.set_annotations(annotations),
        tmin=t_min,
        tmax=t_max,
        metadata=metadata.loc[:, ["stimulus", "category", "trial_type", "RT"]],
    )
