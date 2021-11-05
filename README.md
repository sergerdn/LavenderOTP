# LavenderOTP
Extract data from Google Authenticator       
based on https://github.com/scito/extract_otp_secret_keys

## Install deps:
- install poetry from https://python-poetry.org/
- install python deps:
```bash
poetry install
```
- install `make`
### How to:
- put your images with ocr codes to data/src
- run:
```bash
make 
```
- grab your data from data/dst_dir