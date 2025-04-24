FROM ubuntu:trusty
LABEL org.opencontainers.image.authors="Thomas Kent <docker@teeks99.com>"

# Enable PPA
RUN apt-get update \
 && apt-get install -y software-properties-common \
 && add-apt-repository -y ppa:ubuntu-toolchain-r/test \

# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
  build-essential \

# Install Tool
  gcc-5 \
  g++-5 

