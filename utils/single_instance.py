"""Single-instance helper for Worklog Manager."""

from __future__ import annotations

import logging
import socket
import sys
import threading
import time
from typing import Callable, Optional

_DEFAULT_PORT = 51237
_DEFAULT_TOKEN = "worklog-manager-activate"


class SingleInstanceManager:
    """Coordinate single-instance enforcement across processes."""

    def __init__(
        self,
        *,
        port: int = _DEFAULT_PORT,
        token: str = _DEFAULT_TOKEN,
    ) -> None:
        self.port = port
        self.token = token.encode("utf-8")
        self._server_socket: Optional[socket.socket] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._activation_callback: Optional[Callable[[], None]] = None
        self._is_primary = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    @property
    def is_primary(self) -> bool:
        return self._is_primary

    def acquire(self) -> bool:
        """Attempt to become the primary instance."""
        with self._lock:
            if self._is_primary:
                return True

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sys.platform.startswith("win"):
                exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
                if exclusive is not None:
                    sock.setsockopt(socket.SOL_SOCKET, exclusive, 1)
            else:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                reuse_port = getattr(socket, "SO_REUSEPORT", None)
                if reuse_port is not None:
                    sock.setsockopt(socket.SOL_SOCKET, reuse_port, 1)

            try:
                sock.bind(("127.0.0.1", self.port))
            except OSError as exc:
                sock.close()
                self.logger.debug("Single-instance lock unavailable: %s", exc)
                self._is_primary = False
                return False

            sock.listen(1)
            self._server_socket = sock
            self._is_primary = True

            self._listener_thread = threading.Thread(target=self._listen, daemon=True)
            self._listener_thread.start()
            self.logger.debug("Single-instance listener started on port %s", self.port)
            return True

    def set_activation_callback(self, callback: Optional[Callable[[], None]]) -> None:
        self._activation_callback = callback

    def notify_existing(self, attempts: int = 4, delay: float = 0.25) -> bool:
        """Send an activation request to the running instance."""
        for attempt in range(1, attempts + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                try:
                    client.connect(("127.0.0.1", self.port))
                    client.sendall(self.token)
                    return True
                except OSError as exc:
                    self.logger.debug(
                        "Activation attempt %s/%s failed: %s", attempt, attempts, exc
                    )
            if attempt < attempts:
                time.sleep(delay)
        return False

    def release(self) -> None:
        """Release the primary instance resources."""
        with self._lock:
            self._is_primary = False
            if self._server_socket:
                try:
                    self._server_socket.close()
                except OSError:
                    pass
                finally:
                    self._server_socket = None

    def _listen(self) -> None:
        while self._is_primary and self._server_socket:
            try:
                conn, _addr = self._server_socket.accept()
            except OSError:
                break

            with conn:
                try:
                    payload = conn.recv(1024)
                except OSError:
                    continue

            if payload == self.token:
                callback = self._activation_callback
                if callback:
                    thread = threading.Thread(target=self._invoke_callback, args=(callback,), daemon=True)
                    thread.start()

        self.logger.debug("Single-instance listener stopped")

    def __del__(self) -> None:
        try:
            self.release()
        except Exception:
            pass

    def _invoke_callback(self, callback: Callable[[], None]) -> None:
        try:
            callback()
        except Exception:
            self.logger.exception("Error running activation callback")
