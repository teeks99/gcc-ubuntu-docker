FROM ubuntu:trusty
LABEL org.opencontainers.image.authors="Thomas Kent <docker@teeks99.com>"

# Enable future toolchain PPA
RUN apt-get update \
 && apt-get install -y python-software-properties \

# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
 build-essential \

# Install Tool
  gcc-4.7 \
  g++-4.7
