FROM ubuntu:xenial
MAINTAINER Thomas Kent <docker@teeks99.com>

# Pre-Req Repos
RUN apt-get update \
 && apt-get install -y software-properties-common \
# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
  ca-certificates \
  build-essential \
# Enable Compiler Repo
 && add-apt-repository -y ppa:ubuntu-toolchain-r/test \
# Install Tool
 && apt-get update \
 && apt-get install -y gcc-7 g++-7

