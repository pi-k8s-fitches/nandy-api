MACHINE=$(shell uname -m)
IMAGE=pi-k8s-fitches-nandy-api
VERSION=0.1
TAG="$(VERSION)-$(MACHINE)"
ACCOUNT=gaf3
NAMESPACE=fitches
VOLUMES=-v ${PWD}/openapi/:/opt/pi-k8s/openapi/ -v ${PWD}/settings.yaml.example/:/etc/pi-k8s/settings.yaml -v ${PWD}/lib/:/opt/pi-k8s/lib/ -v ${PWD}/test/:/opt/pi-k8s/test/ -v ${PWD}/bin/:/opt/pi-k8s/bin/
PORT=7865

ifeq ($(MACHINE),armv7l)
BASE=resin/raspberry-pi-alpine-python:3.6.1
else
BASE=python:3.6-alpine3.8
endif

.PHONY: build shell test run push config create update delete config-dev create-dev update-dev delete-dev

clone:
	git clone git@github.com:pi-k8s-fitches/nandy-data.git

build:
	cd nandy-data && git pull && cd ..
	docker build . --build-arg BASE=$(BASE) -t $(ACCOUNT)/$(IMAGE):$(TAG)

shell:
	docker run -it $(VARIABLES) $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(TAG) sh

test:
	TAG=${TAG} docker-compose -f docker-compose-test.yml up --abort-on-container-exit --exit-code-from unittest

run:
	MACHINE=${MACHINE} TAG=${TAG} docker-compose -f docker-compose.yml up

push: build
	docker push $(ACCOUNT)/$(IMAGE):$(TAG)

config:
	kubectl create configmap -n fitches chore-api --dry-run --from-file=config/settings.yaml -o yaml | kubectl -n fitches --context=pi-k8s apply -f -

create:
	kubectl --context=pi-k8s create -f k8s/pi-k8s.yaml

delete:
	kubectl --context=pi-k8s delete -f k8s/pi-k8s.yaml

update: delete create

config-dev:
	kubectl create configmap -n fitches chore-api --dry-run --from-file=config/settings.yaml -o yaml | kubectl -n fitches --context=minikube apply -f -

create-dev:
	kubectl --context=minikube create -f k8s/minikube.yaml

delete-dev:
	kubectl --context=minikube delete -f k8s/minikube.yaml

update-dev: delete-dev create-dev
