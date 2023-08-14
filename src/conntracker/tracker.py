"""Track connections opened by functions and/or processes."""
import functools
import os
import sys
import threading
import time
import warnings

from collections import defaultdict
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, DefaultDict, Optional, Set, TextIO, Type, TypeVar, Union

import psutil


RT = TypeVar("RT")


def warn_if_not_privileged() -> None:
    """Emit a usage warning because some features may not work otherwise."""
    if sys.platform == "darwin" and os.geteuid() != 0:
        warnings.warn(
            "Darwin platform users need to run this script as a privileged user.",
            category=UserWarning,
            stacklevel=2,
        )


class ConnTracker:
    """
    Socket connection monitoring class.

    Typical usage is:

    ```python
    from monitor import ConnTracker

    tracker = ConnTracker()
    with tracker:
        # run your functions inside the context
        ...
    print(tracker)  # show the opened socket connections
    ```
    """

    def __init__(
        self,
        pid: Optional[int] = None,
        *,
        interval: Optional[float] = None,
        track_children: bool = True,
    ) -> None:
        """
        Create a new `ConnTracker` instance.

        Parameters
        ----------
        pid : Optional[int]
            The process ID to monitor or the current process if
            no value is given.
        interval : Optional[float]
            The interval at which the tracker should poll for connections.
        track_children : bool
            Whether to track connections opened by child processes
            or not. The default is True.
        """
        warn_if_not_privileged()

        self.proc = psutil.Process(pid=pid or os.getpid())
        self.interval = interval
        self.track_children = track_children

        self.monitor: threading.Thread = threading.Thread(target=self._observe_sockets, daemon=True)
        self.exit_event: threading.Event = threading.Event()
        self.connections: DefaultDict[int, DefaultDict[int, Set[psutil._common.sconn]]]
        self.connections = defaultdict(lambda: defaultdict(set))

    def __enter__(self) -> "ConnTracker":
        self.monitor.start()
        return self

    def __exit__(self, exc_type: Type[Exception], exc_inst: Exception, exc_tb: TracebackType) -> None:
        self.exit_event.set()
        if self.monitor.is_alive():
            self.monitor.join()

    def __repr__(self) -> str:
        self_repr = f"{self.__class__.__name__} summary:\n"
        for pid, pid_conns in self.connections.items():
            pid_str = f"PID {pid}"
            if pid == self.proc.pid:
                pid_str += " (main)"
            self_repr += f"{pid_str}:\n"

            for _, fd_conns in pid_conns.items():
                for conn in fd_conns:
                    prefix = f"{conn.family.name} - {conn.status}".ljust(25)

                    if len(conn.laddr) == 2:
                        local_addr = f"{conn.laddr[0]}::{conn.laddr[1]}"  # type: ignore
                    else:
                        local_addr = "unknown"
                    local_addr = local_addr.rjust(46)

                    if len(conn.raddr) == 2:
                        remote_addr = f"{conn.raddr[0]}::{conn.raddr[1]}"  # type: ignore
                    else:
                        remote_addr = "none"

                    self_repr += f"    * {prefix}: {local_addr} -> {remote_addr}\n"

        return self_repr

    def _observe_sockets(self) -> None:
        while not self.exit_event.is_set():
            all_procs = [self.proc]
            if self.track_children:
                with suppress(psutil.NoSuchProcess):
                    child_procs = self.proc.children(recursive=True)
                    all_procs += child_procs

            proc_pids = {proc.pid for proc in all_procs}

            try:
                connections = psutil.net_connections()
            except psutil.AccessDenied:
                continue

            for conn in connections:
                if conn.pid in proc_pids:
                    self.connections[conn.pid][conn.fd].add(conn)

            if self.interval:
                time.sleep(self.interval)


def trackconn(
    func: Callable[..., RT],
    *,
    stream: Optional[Union[str, Path, TextIO]] = None,
    interval: Optional[float] = None,
    track_children: bool = True,
) -> Callable[..., RT]:
    """
    Decorate a function to monitor all of the connections it makes.

    Parameters
    ----------
    stream : Optional[Union[str, Path, TextIO]]
        The output file path or stream to write tracked connection
        information to.
    interval : Optional[float]
        The interval at which the connections should be tracked.
    track_children : bool
        Whether or not to track connections opened by child processes.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> RT:
        tracer = ConnTracker(interval=interval, track_children=track_children)
        with tracer:
            retval = func(*args, **kwargs)

        nonlocal stream
        if isinstance(stream, (str, Path)):
            with open(stream, "w", encoding="utf-8") as out:
                out.write(repr(tracer))
        else:
            if stream is None:
                stream = sys.stdout
            stream.write(repr(tracer))

        return retval

    return wrapper
