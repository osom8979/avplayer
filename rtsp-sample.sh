#!/usr/bin/env bash

docker run --rm -it \
    -e ENABLE_TIME_OVERLAY=true \
    -e RTSP_PORT=9999 \
    -p 9999:9999 \
    ullaakut/rtspatt
