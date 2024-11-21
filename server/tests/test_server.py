import io
import json
import zipfile
import hashlib
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.server import app, VideoMetadata

client = TestClient(app)


@pytest.fixture
def mock_mongodb():
    with patch("server.server.MongoClient") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.get_default_database.return_value = mock_db
        yield mock_db


import os


@pytest.fixture
def sample_zip_data():
    # Path to the sample zip file
    zip_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "sample_data",
        "dynamic_outdoor_xyzMovement_morning2.zip",
    )

    # Read the zip file
    with open(zip_path, "rb") as zip_file:
        return zip_file.read()


@pytest.fixture
def mock_subprocess():
    with patch("server.server.subprocess") as mock_subproc:
        yield mock_subproc


@pytest.fixture
def mock_open():
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = (
            b"fake thumbnail data"
        )
        yield mock_open


def test_upload_data(mock_mongodb, sample_zip_data):
    # Calculate the correct hash for the sample data
    correct_hash = hashlib.sha256(sample_zip_data).hexdigest()

    response = client.post(
        "/api/upload",
        params={"user_id": "test_user", "data_hash": correct_hash},
        files={"zip_data": ("test.zip", sample_zip_data, "application/zip")},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    # Check if MongoDB insert was called
    mock_mongodb.videos.insert_one.assert_called_once()


def test_upload_data_hash_mismatch(sample_zip_data, mock_mongodb):
    response = client.post(
        "/api/upload",
        params={"user_id": "test_user", "data_hash": "wrong_hash"},
        files={"zip_data": ("test.zip", sample_zip_data, "application/zip")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Data hash mismatch"}


def test_list_videos(mock_mongodb):
    mock_videos = [
        {
            "data_hash": "123",
            "user_id": "test_user",
            "time_start": datetime.now(),
            "time_end": datetime.now(),
            "map_start": {"lat": 0.0, "lon": 0.0},
            "map_end": {"lat": 0.0, "lon": 0.0},
            "thumbnail": b"fake thumbnail",
            "raw_data_url": "/data/123.zip",
            "video_url": "/data/123_web.mp4",
        }
    ]
    mock_mongodb.videos.find.return_value = mock_videos

    response = client.get("/api/list", params={"user_id": "test_user"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["data_hash"] == "123"

    mock_mongodb.videos.find.assert_called_once_with({"user_id": "test_user"})


# TODO: Add more tests for edge cases and error handling
