import cv2


def test_opencv_major_version_is_5():
    # Competition rule: OpenCV 5 must be a substantive runtime component
    # (docs/OPEN_QUESTIONS.md). Guards against an accidental 4.x install.
    assert cv2.__version__.split(".")[0] == "5", cv2.__version__
