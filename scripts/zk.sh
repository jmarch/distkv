#!/bin/bash

docker run -it --rm --network distkv --link zoo1:zookeeper zookeeper zkCli.sh -server zookeeper
