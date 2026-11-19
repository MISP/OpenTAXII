# Example Makefile for creating the docker image

.PHONY: all build

REG:="eclecticiq"
IMAGE:="opentaxii"

all: build

build:
	docker build -t $(REG)/$(IMAGE) ../.
