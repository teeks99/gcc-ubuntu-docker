FROM ubuntu:trusty
MAINTAINER Thomas Kent <teeks99@yahoo.com>

# Enable PPA
RUN apt-get update \
 && apt-get install -y software-properties-common \
 && add-apt-repository -y ppa:ubuntu-toolchain-r/test \

# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
  build-essential \

# Install Tool
  gcc-6 \
  g++-6
