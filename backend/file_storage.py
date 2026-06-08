import os
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

import models


UPLOAD_DIR = "/tmp/uploads" if os.getenv("RENDER") == "true" or os.getenv("VERCEL") == "1" else "uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def dataset_path(owner_id: int, filename: str) -> str:
    safe_filename = os.path.basename(filename)
    return str(Path(UPLOAD_DIR) / f"{owner_id}_{safe_filename}")


def store_dataset_file(db: Session, dataset: models.Dataset, content: bytes) -> None:
    file_record = db.get(models.DatasetFile, dataset.id)
    if file_record:
        file_record.content = content
    else:
        db.add(models.DatasetFile(dataset_id=dataset.id, content=content))


def ensure_dataset_file(db: Session, dataset: models.Dataset) -> str:
    if os.path.exists(dataset.filepath):
        return dataset.filepath

    file_record = db.get(models.DatasetFile, dataset.id)
    if not file_record:
        raise HTTPException(status_code=404, detail="Dataset file is missing. Please delete this stale dataset and upload it again.")

    Path(dataset.filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(dataset.filepath, "wb") as file_object:
        file_object.write(file_record.content)

    return dataset.filepath


def refresh_dataset_file(db: Session, dataset: models.Dataset) -> None:
    if not os.path.exists(dataset.filepath):
        raise HTTPException(status_code=404, detail="Dataset file is missing. Please upload it again.")

    with open(dataset.filepath, "rb") as file_object:
        store_dataset_file(db, dataset, file_object.read())
