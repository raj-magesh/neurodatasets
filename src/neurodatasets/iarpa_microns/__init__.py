from pathlib import Path

from neurodatasets._utilities import NEURODATASETS_HOME

from neurodatasets.files import s3

IDENTIFIER = "iarpa.microns"
CACHE_PATH = NEURODATASETS_HOME / IDENTIFIER


def download() -> None:
    filename = "functional_data_database_container_image_v8.tar"
    s3.download(
        Path(
            "iarpa_microns/minnie/functional_data/two_photon_processed_data_and_metadata/database_v8/functional_data_database_container_image_v8.tar",
        ),
        local_path=CACHE_PATH / "downloads" / filename,
        bucket="bossdb-open-data",
    )


if __name__ == "__main__":
    download()

    # Run the following command to extract the OCI container
    # podman load --input functional_data_database_container_image_v8.tar
