FROM ubuntu:xenial
MAINTAINER Thomas Kent <docker@teeks99.com>

# Pre-Req Repos
RUN apt-get update \
 && apt-get install -y software-properties-common \
 && add-apt-repository -y ppa:git-core/ppa \
# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
  ca-certificates \
  build-essential \
  git \
  wget \
  python2.7 \
  python2.7-dev \
  python3.5 \
  python3.5-dev \
  libbz2-dev \
  zlib1g-dev \
 && cd /usr/bin \
 && ln -s python2.7 python \
# Speed up fetch
 && git config --global submodule.fetchJobs 40
# Enable Compiler Repo
RUN add-apt-repository -y ppa:ubuntu-toolchain-r/test \
# Install Tool
 && apt-get update \
 && apt-get install -y gcc-7 g++-7

