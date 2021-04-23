FROM ubuntu:focal
MAINTAINER Thomas Kent <docker@teeks99.com>

# Pre-Req Repos
RUN apt-get update \
 && apt-get install -y software-properties-common \
 && add-apt-repository -y ppa:ubuntu-toolchain-r/ppa \
# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
  ca-certificates \
  build-essential \
# Install Tool
  gcc-10 \
  g++-10

