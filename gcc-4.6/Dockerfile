FROM ubuntu:precise
MAINTAINER Thomas Kent <teeks99@yahoo.com>

# Enable future toolchain PPA
RUN apt-get update && apt-get install -y python-software-properties && add-apt-repository -y ppa:git-core/ppa #&& add-apt-repository -y ppa:ubuntu-toolchain-r/test

# Install pre-reqs
RUN apt-get update && apt-get install -y \
 build-essential \
 git \
 wget \
 python2.7 \
 python2.7-dev \
 python3.2 \
 python3.2-dev \
 libbz2-dev \
 zlib1g-dev

# Install Tool
RUN apt-get update && apt-get install -y gcc-4.6 g++-4.6
