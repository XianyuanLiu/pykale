import os
from pathlib import Path

import pytest

from kale.utils.download import download_file_by_url

output_directory = Path().absolute().parent.joinpath("test_data/download")
PARAM = [
    " https://github.com/pykale/data/raw/main/video_data/video_test_data/ADL/annotations/labels_train_test/adl_P_11_train.pkl;a.pkl;pkl",
    " https://github.com/pykale/data/raw/main/video_data/video_test_data.zip;video_test_data.zip;zip",
]


@pytest.mark.parametrize("param", PARAM)
def test_download_file_by_url(param):
    url, output_file_name, file_format = param.split(";")

    # run twice to test the code when the file exist
    download_file_by_url(url, output_directory, output_file_name, file_format)
    download_file_by_url(url, output_directory, output_file_name, file_format)

    assert os.path.exists(output_directory.joinpath(output_file_name)) is True
