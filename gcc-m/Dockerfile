FROM ubuntu:jammy
MAINTAINER Thomas Kent <docker@teeks99.com>
ARG gccver=mainline
ARG suffix=m

# Pre-Req Repos
RUN set -x \
 && apt-get update \
 && apt-get install -y software-properties-common \
# Install pre-reqs
 && apt-get update \
 && apt-get install -y \
  ca-certificates \
  build-essential \
  git \
# User requested
  apt-utils \
  dialog \  
  locales \
  wget \
# Install Tool
  m4 \
  flex \
  bison \
 && mkdir /src \
 && cd /src \
 && git clone --depth 1 --branch master git://gcc.gnu.org/git/gcc.git gcc-${gccver} \
 && cd gcc-${gccver} \
 && contrib/download_prerequisites \
 && cd .. \
 && mkdir build \
 && cd build \
 && ../gcc-${gccver}/configure \
  -v \
  --enable-checking=release \
  --enable-shared \
  --enable-threads=posix \
  --enable-__cxa_atexit \
  --enable-clocale=gnu \
  --enable-languages=c,c++ \
  --disable-multilib \
  --bindir=/usr/bin \
  --prefix=/usr/local/gcc-${gccver} \
  --program-suffix=-${suffix} \
 && make -j`nproc` \
 && make install-strip \
 && echo /usr/local/gcc-${gccver}/lib64 > /etc/ld.so.conf.d/gcc-${gccver}.conf \
 && cd / \
 && rm -rf src