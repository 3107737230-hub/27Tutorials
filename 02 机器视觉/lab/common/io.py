from pathlib import Path
import math
import cv2
import numpy as np
import matplotlib.pyplot as plt

def read_image(path, gray=False):
    """从中文或英文路径读图；返回 OpenCV 的 BGR 或单通道灰度数组。"""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"找不到图片：{path}")
    data = np.fromfile(str(path), dtype=np.uint8)
    flags = cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR
    image = cv2.imdecode(data, flags)
    if image is None:
        raise ValueError(f"图片解码失败：{path}")
    return image

def save_image(path, image):
    """编码后写入，兼容中文路径；只接受用于展示的 uint8 图像。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if image.dtype != np.uint8:
        raise TypeError("请先把图像转换到 uint8，再保存；不要直接保存有符号梯度。")
    ok, encoded = cv2.imencode(path.suffix, image)
    if not ok:
        raise OSError(f"图片编码失败：{path}")
    encoded.tofile(str(path))
    return path

def show_images(images, cols=3, size=4, save_to=None):
    """images 是 {英文标题: 图像}；灰度固定显示范围 0~255，避免自动拉伸。"""
    rows = math.ceil(len(images) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * size, rows * size), squeeze=False)
    for ax, (title, image) in zip(axes.flat, images.items()):
        if image.ndim == 2:
            ax.imshow(image, cmap="gray", vmin=0, vmax=255)
        else:
            ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        ax.set_title(title)
        ax.axis("off")
    for ax in list(axes.flat)[len(images):]:
        ax.axis("off")
    fig.tight_layout()
    if save_to:
        Path(save_to).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_to, dpi=120, bbox_inches="tight")
    plt.show()
    plt.close(fig)
