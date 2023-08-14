"""Test that the decorator functionality works."""
import io
import socket

from typing import Tuple

from conntracker import trackconn
from conntracker.testing import echo_server, warnings_catcher


def send_stuff(addr: Tuple[str, int]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(addr)
        msg = b"Nothing interesting here."
        for _ in range(10):
            sock.send(msg)


def test_trackconn() -> None:
    """Test that something is tracked by the tracker."""
    stream = io.StringIO()
    func = trackconn(send_stuff, stream=stream)

    with warnings_catcher():
        with echo_server() as addr:
            func(addr)

    retval = stream.getvalue()
    assert len(retval.split("\n")) > 1, f"Output:\n{retval}\n--"


if __name__ == "__main__":
    test_trackconn()
