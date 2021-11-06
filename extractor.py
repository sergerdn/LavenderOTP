import logging
import os

import typer

from ocr.worker import LavenderOcrWorker

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("[lavender-otp]")

ABS_PATH = os.path.dirname(os.path.abspath(__file__))

app = typer.Typer()


@app.command()
def extract(src_dir: str, dst_dir: str):
    typer.echo(f"Running with src_dir: {src_dir}, dst_dir: {dst_dir}...")
    worker = LavenderOcrWorker(src_dir=src_dir, dst_dir=dst_dir)
    if not worker.ocr():
        logger.error("failed ocr")
        return

    if not worker.otp():
        logger.error("failed otp")
        return


if __name__ == "__main__":
    app()
