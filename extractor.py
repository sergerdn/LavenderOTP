import copy
import logging
import os
import pdb
from typing import Union
import glob
from urllib.parse import urlparse, parse_qs
import base64
from PIL import Image
from pyzbar import pyzbar
from PIL import UnidentifiedImageError
from proto.v1.gauth_pb2 import MigrationPayload
import typer
from copy import deepcopy

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("[lavender-otp]")

ABS_PATH = os.path.dirname(os.path.abspath(__file__))

app = typer.Typer()


class LavenderOcrWorker(object):
    src_dir: str
    found = False
    filename_ocr = []

    def __init__(self, src_dir: str, dst_dir: str):
        self.src_dir = src_dir
        self.dst_dir = dst_dir

    def ocr(self):
        self.src_dir = self._norm_dir(self.src_dir)
        if not self.src_dir:
            return
        self.dst_dir = self._norm_dir(self.dst_dir)
        if not self.dst_dir:
            return

        for filename in self._get_files():
            for data in self._get_text(filename):
                self.found = True
                dst_filename = os.path.join(self.dst_dir, "%s.txt" % os.path.basename(filename))
                with open(dst_filename, "wb") as fp:
                    fp.write(data)
                    fp.write(b"\n")
                logger.debug(f"wrote data from file: {os.path.basename(filename)}")
                self.filename_ocr.append(dst_filename)

        return self.found

    def otp(self):
        self.found = False
        for filename in self.filename_ocr:
            with open(filename, "rb") as fp:
                for line in fp:
                    line = line.strip()
                    parsed_url = urlparse(line)
                    params = parse_qs(parsed_url.query)
                    data = params.get(b"data")
                    if not data or len(data) == 0:
                        logger.error(f"wrong data: {line}")
                        continue

                    data_encoded = data[0]
                    data = base64.b64decode(data_encoded)
                    payload = MigrationPayload()
                    payload.ParseFromString(data)
                    dst_filename = os.path.join(self.dst_dir, "%s.accounts.txt" % os.path.basename(filename))
                    with open(dst_filename, "w") as fp:
                        for find in payload.otp_parameters:
                            self.found = True
                            fp.write(f"#################################\n")
                            secret = str(base64.b32encode(find.secret), 'utf-8').replace('=', '')
                            fp.write(f"secret: {secret}\n")
                            fp.write(f"name: {find.name}\n")
                            fp.write(f"issuer: {find.issuer}\n")
                            fp.write(f"algorithm: {find.algorithm}\n")
                            fp.write(f"digits: {find.digits}\n")
                            fp.write(f"type:: {find.type:}\n")

        return self.found

    def _norm_dir(self, src_dir) -> Union[str, bool]:
        if not os.path.isabs(src_dir):
            src_dir = os.path.abspath(src_dir)
        src_dir = os.path.normpath(src_dir)

        logger.debug(f"resolved dir to: {src_dir}")
        if not os.path.exists(src_dir) or not os.path.isdir(src_dir):
            logger.error(f"doesn't exists or not dir: {src_dir}")
            return False

        return src_dir

    def _get_files(self):
        for filename in glob.glob(os.path.join(self.src_dir, "*.*")):
            if filename == ".gitignore":
                continue
            filename = os.path.join(self.src_dir, filename)
            yield filename

    def _get_text(self, filename):
        try:
            img = Image.open(filename)
        except UnidentifiedImageError as ex:
            logger.error(ex)
            return

        output = pyzbar.decode(img)
        if len(output) == 0:
            logger.warning(f"skipped because can't decoded: {filename}")
            return
        for one in output:
            if one.data.startswith(b"otpauth-migration://"):
                yield one.data


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
