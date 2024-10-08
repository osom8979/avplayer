# avplayer

[![PyPI](https://img.shields.io/pypi/v/avplayer?style=flat-square)](https://pypi.org/project/avplayer/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/avplayer?style=flat-square)
[![GitHub](https://img.shields.io/github/license/osom8979/avplayer?style=flat-square)](https://github.com/osom8979/avplayer/)

PyAV Media Player

## Installation

Install `avplayer`:

```shell
pip install avplayer
```

If you want to use the [tk](https://docs.python.org/3/library/tkinter.html) preview:

```shell
pip install avplayer[Pillow]
```

## Commandline Tools

```shell
python -m avplayer --help
```

## Realtime support

If it is important to get the latest frame in real-time streaming
such as RTSP streaming, we recommend adjusting the `--drop-*` related options.

```bash
python -m avplayer --drop-slow-frame --drop-threshold=1 ...
```

The `cvplayer.avconfig.AvConfig` class can be used as follows:

```python
from avplayer.avconfig import AvConfig

config = AvConfig(
    input_file="rtsp://...",
    drop_slow_frame=True,
    drop_threshold=1,
)
```

## Features

### [opencv-python](https://pypi.org/project/opencv-python/) compatibility

To prevent freeze when using opencv-python's imshow,
do not use `import av` at file-scope.

Please refer to the following link:
* [AV import leads to OpenCV imshow freeze · Issue #21952 · opencv/opencv](https://github.com/opencv/opencv/issues/21952)
* [python - Can't show image with opencv when importing av - Stack Overflow](https://stackoverflow.com/questions/72604912/cant-show-image-with-opencv-when-importing-av)

## Examples

### AioCv

See the [examples/aio_cv.py](./examples/aio_cv.py) file.

### OpenCV highgui

See the [examples/cv2_example.py](./examples/cv2_example.py) file.

## License

See the [LICENSE](./LICENSE) file for details. In summary,
**avplayer** is licensed under the **MIT license**.
