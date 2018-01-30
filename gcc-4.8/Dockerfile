FROM ubuntu:trusty
MAINTAINER Thomas Kent <teeks99@yahoo.com>

# Enable future toolchain PPA
RUN apt-get update \
 && apt-get install -y software-properties-common \
 && add-apt-repository -y ppa:ubuntu-toolchain-r/test \

# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
  build-essential \

# Install Tool
  gcc-4.8 \
  g++-4.8
