FROM ubuntu:precise
MAINTAINER Thomas Kent <teeks99@yahoo.com>

# Enable future toolchain PPA
RUN apt-get update && apt-get install -y python-software-properties && add-apt-repository -y ppa:ubuntu-toolchain-r/test

# Install pre-reqs
RUN apt-get update && apt-get install -y \
 build-essential

# Install Tool
RUN apt-get update && apt-get install -y gcc-4.7 g++-4.7
