.PHONY: all test proto otp

GIT_COMMIT := $(shell git rev-list -1 HEAD)
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_VERSION := $(shell git describe --tags --always)
BUILD_DATE := $(shell date -u +%Y-%m-%dT%H:%M:%S)

all:
	$(MAKE) proto

proto:
	protoc --python_out=.  proto/v1/gauth.proto

otp:
	python extractor.py data/src_dir data/dst_dir