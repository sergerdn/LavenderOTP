import base64
import glob
import logging
import os
from typing import Union
from urllib.parse import urlparse, parse_qs

from PIL import Image
from PIL import UnidentifiedImageError
from pydantic import ValidationError
from pyzbar import pyzbar

from ocr.models import OtpEntry
from proto.v1.gauth_pb2 import MigrationPayload

logger = logging.getLogger("[lavender-otp]")


class LavenderOcrWorker(object):
    src_dir: str
    found = False
    filename_ocr = []

    def __init__(self, src_dir: str, dst_dir: str):
        self.src_dir = src_dir
        self.dst_dir = dst_dir

    def ocr(self) -> bool:
        if not self._norm_dir(self.src_dir):
            return False

        if not self.dst_dir:
            return False

        for filename in self._get_files():
            for data in self._get_text(filename):
                self.found = True
                dst_filename = os.path.join(self.dst_dir, "%s.txt" % os.path.basename(filename))
                with open(dst_filename, "wb") as fp_dst:
                    fp_dst.write(data)
                    fp_dst.write(b"\n")
                logger.debug("wrote data from file: %s" % os.path.basename(filename))
                self.filename_ocr.append(dst_filename)

        return self.found

    def otp(self):
        self.found = False
        for filename in self.filename_ocr:
            with open(filename, "rb") as fp_ocr:
                for line in fp_ocr:
                    line = line.strip()
                    parsed_url = urlparse(line)
                    params = parse_qs(parsed_url.query)
                    data = params.get(b"data")
                    if not data or len(data) == 0:
                        logger.error("wrong data: %s" % line)
                        continue

                    data_encoded = data[0]
                    data = base64.b64decode(data_encoded)
                    payload = MigrationPayload()
                    payload.ParseFromString(data)
                    dst_filename = os.path.join(self.dst_dir, "%s.accounts.txt" % os.path.basename(filename))
                    with open(dst_filename, "w") as fp_ocr:
                        for item in payload.otp_parameters:
                            self.found = True

                            secret = str(base64.b32encode(item.secret), "utf-8").replace("=", "")
                            try:
                                entry = OtpEntry(
                                    secret=secret,
                                    name=item.name,
                                    issuer=item.issuer,
                                    algorithm=item.algorithm,
                                    digits=item.digits,
                                    type=item.type,
                                )
                            except ValidationError:
                                logger.error("invalid entry: %s", item)
                                continue

                            fp_ocr.write("#################################\n")
                            fp_ocr.write(f"secret: {entry.secret}\n")
                            fp_ocr.write(f"name: {entry.name}\n")
                            fp_ocr.write(f"issuer: {entry.issuer}\n")
                            fp_ocr.write(f"algorithm: {entry.algorithm}\n")
                            fp_ocr.write(f"digits: {entry.digits}\n")
                            fp_ocr.write(f"type:: {entry.type:}\n")
                            fp_ocr.flush()

        return self.found

    def _norm_dir(self, src_dir) -> Union[str, bool]:
        if not os.path.isabs(src_dir):
            src_dir = os.path.abspath(src_dir)
        src_dir = os.path.normpath(src_dir)

        logger.debug(f"resolved dir to: {src_dir}")
        if not os.path.exists(src_dir) or not os.path.isdir(src_dir):
            logger.error(f"doesn't exists or not dir: {src_dir}")
            return False

        self.src_dir = src_dir

        return True

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
            logger.warning("skipped because can't decoded: %s" % filename)
            return
        for one in output:
            if one.data.startswith(b"otpauth-migration://"):
                yield one.data
