FROM ubuntu:trusty
MAINTAINER Thomas Kent <teeks99@yahoo.com>

# Enable future toolchain PPA
RUN apt-get update \
 && apt-get install -y python-software-properties \

# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
  build-essential \

# Install Tool
  gcc-4.6 \
  g++-4.6
