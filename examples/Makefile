# Example Makefile for creating the docker image

.PHONY: all build

IMAGE ?= opentaxii:local

all: build

build:
	docker build -t $(IMAGE) ..
