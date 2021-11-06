# LavenderOTP (proof of concept)

LavenderOTP extract secret keys from Google Authenticator exported images.  
based on https://github.com/scito/extract_otp_secret_keys

### Usage:

- export the QR codes from "Google Authenticator" app and save it as images to **data/src_dir**:   
  ![Example Export!](./docs/example_export.jpeg "Example export")
- install deps:

    1. install poetry from https://python-poetry.org/
    2. install python deps:
  ```bash 
  poetry install --no-dev
  ```
    3. install `make`

- run:

```bash
make 
```

- **grab your data from data/dst_dir**