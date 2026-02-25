from pathlib import Path

from spleeter.separator import Separator

SAMPLE_DIR = Path("data/sample")
SOURCE_DIR = Path("data/source")
OUTPUT_DIR = Path("data/output")


def split_to_vocal_and_accompaniment(source_path: Path, output_dir: Path) -> tuple[Path, Path]:
    if source_path.suffix.lower() != ".mp3":
        raise ValueError("Only .mp3")

    if not source_path.exists():
        raise FileNotFoundError("File not found")

    output_dir.mkdir(parents=True, exist_ok=True)
    separator = Separator("spleeter:2stems", multiprocess=False)
    separator.separate_to_file(str(source_path), str(output_dir))

    name = source_path.stem
    vocal_path = output_dir / name / "vocals.wav"
    accompaniment_path = output_dir / name / "accompaniment.wav"

    if not vocal_path.exists() or not accompaniment_path.exists():
        raise RuntimeError("Failed to split audio")

    return vocal_path, accompaniment_path
