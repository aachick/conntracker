"""Methods for testing the library code-base."""
import contextlib
import multiprocessing as mp
import socket
import sys
import time

from multiprocessing.synchronize import Event
from typing import Iterator, Tuple, cast


def warnings_catcher():  # type: ignore
    """Return a custom warnings catcher based on the platform."""
    warnings = (UserWarning,) if sys.platform == "darwin" else ()
    if warnings:
        import pytest

        return pytest.warns(warnings)

    return contextlib.nullcontext()


def get_free_port() -> int:
    """Get a free port for testing."""
    with socket.socket() as sock:
        sock.bind(("", 0))
        port = sock.getsockname()[1]
    return cast(int, port)


def _echo_server(
    addr: Tuple[str, int],
    family: socket.AddressFamily,
    kind: socket.SocketKind,
    stop_evt: Event,
) -> None:
    with socket.socket(family, kind) as sock:
        sock.bind(addr)
        sock.listen()
        conn, _ = sock.accept()
        with conn:
            while True:
                if stop_evt.is_set():
                    break

                try:
                    data = conn.recv(1024)
                    conn.sendall(data)
                except OSError:
                    continue


@contextlib.contextmanager
def echo_server(
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    family: socket.AddressFamily = socket.AF_INET,
    kind: socket.SocketKind = socket.SOCK_STREAM,
) -> Iterator[Tuple[str, int]]:
    """Run a echo server in the background and yield its connection info."""
    port = port or get_free_port()
    addr = (host, port)

    stop_evt = mp.Event()
    proc = mp.Process(
        target=_echo_server,
        args=(addr, family, kind, stop_evt),
        daemon=True,
    )
    try:
        proc.start()
        time.sleep(0.5)
        yield addr
    finally:
        stop_evt.set()
        if proc.is_alive():
            proc.join()
