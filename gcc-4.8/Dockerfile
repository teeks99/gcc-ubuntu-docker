FROM ubuntu:trusty
MAINTAINER Thomas Kent <teeks99@yahoo.com>

# Enable future toolchain PPA
RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:ubuntu-toolchain-r/test

# Install pre-reqs
RUN apt-get update && apt-get install -y \
 build-essential

# Install Tool
RUN apt-get update && apt-get install -y gcc-4.8 g++-4.8
