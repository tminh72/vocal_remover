from pathlib import Path

from app.db import get_conn
from app.services.audio_processing import OUTPUT_DIR, split_to_vocal_and_accompaniment
from app.worker.celery_app import celery_app


@celery_app.task(name="process_audio")
def process_audio(record_id: str, source_path: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE audio_tasks SET status = ? WHERE id = ?",
            ("processing", record_id),
        )
        conn.commit()

        vocal_path, accompaniment_path = split_to_vocal_and_accompaniment(Path(source_path), OUTPUT_DIR)

        conn.execute(
            "UPDATE audio_tasks SET status = ?, vocal_path = ?, music_path = ? WHERE id = ?",
            ("completed", str(vocal_path), str(accompaniment_path), record_id),
        )
        conn.commit()
    except Exception as exc:
        conn.execute(
            "UPDATE audio_tasks SET status = ?, log = ? WHERE id = ?",
            ("failed", str(exc), record_id),
        )
        conn.commit()
        raise
    finally:
        conn.close()
