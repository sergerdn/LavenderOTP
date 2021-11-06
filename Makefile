.PHONY: all proto otp
.DEFAULT_GOAL := otp

GIT_COMMIT := $(shell git rev-list -1 HEAD)
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_VERSION := $(shell git describe --tags --always)
BUILD_DATE := $(shell date -u +%Y-%m-%dT%H:%M:%S)

all:
	$(MAKE) proto
	$(MAKE) otp

proto:
	protoc --python_out=.  proto/v1/gauth.proto

clean:
	rm data/dst_dir/*.txt

otp:
	python extractor.py data/src_dir data/dst_dir
	ls -lia data/dst_dir

lint:
	find . -type f -name "*.py" | xargs pylint

lint_fix:
	python -m black .
	autopep8 --in-place --recursive .