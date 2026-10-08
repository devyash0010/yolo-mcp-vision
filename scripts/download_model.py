# """CLI utility to download and verify YOLO weights."""

import argparse
from pathlib import Path
from ultralytics import YOLO


def download_model(model_name: str, target_dir: str):
    target_path = Path(target_dir) / model_name
    target_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[*] Downloading/verifying YOLO model: {model_name}...")
    model = YOLO(model_name)
    # Save a copy to explicit target_path if not already there
    if not target_path.exists():
        import shutil
        downloaded = Path(model.ckpt_path)
        if downloaded.exists() and downloaded.resolve() != target_path.resolve():
            shutil.copy(downloaded, target_path)

    print(f"[+] Model ready at: {target_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YOLO weights")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="YOLO model name")
    parser.add_argument("--dir", type=str, default="models", help="Destination folder")
    args = parser.parse_args()
    download_model(args.model, args.dir)

