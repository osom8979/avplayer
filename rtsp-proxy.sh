#!/usr/bin/env bash

docker run --rm -it \
    -e MTX_PROTOCOLS=tcp \
    -p 8554:8554 \
    -p 1935:1935 \
    -p 8888:8888 \
    -p 8889:8889 \
    bluenviron/mediamtx
