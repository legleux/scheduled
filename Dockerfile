FROM ubuntu:20.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git cmake python3 curl vim-tiny
RUN apt-get install -y python3-pip python-is-python3 pkg-config zlib1g curl

# RUN apt-get install -y gcc-11 g++-11 && \
#         update-alternatives --remove-all cpp && \
#         update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 90 --slave /usr/bin/g++ g++ /usr/bin/g++-9 \
#             --slave /usr/bin/gcov gcov /usr/bin/gcov-9 --slave /usr/bin/gcc-ar gcc-ar /usr/bin/gcc-ar-9 \
#             --slave /usr/bin/gcc-ranlib gcc-ranlib /usr/bin/gcc-ranlib-9  --slave /usr/bin/cpp cpp /usr/bin/cpp-9

COPY install_boost.sh /tmp/install_boost.sh
RUN ./tmp/install_boost.sh 1.77.0
ENV BOOST_ROOT=/opt/boost

COPY install_openssl.sh /tmp/install_openssl.sh
RUN ./tmp/install_openssl.sh
ENV OPENSSL_ROOT=/opt/local/openssl

# RUN git clone --depth 1 --branch "amm-core-functionality" "https://github.com/gregtatcam/rippled.git"
# RUN cmake -S rippled -B rippled/build -Dstatic=OFF -DCMAKE_BUILD_TYPE=Debug -Dunity=Off
# RUN cmake --build rippled/build --parallel $(nproc)

# FROM ubuntu:20.04
# COPY --from=0 /source/build/xbridge_witnessd /opt/xbridge-witness/xbridge_witnessd
# COPY --from=0 /source/example-config.json /opt/xbridge-witness/cfg/example-config.json

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
