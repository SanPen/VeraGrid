# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os
import platform
import subprocess
import time
import urllib.error
import urllib.request
from typing import Optional


class OllamaProcessManager:
    """
    Detect and launch a local Ollama server when VeraGrid is configured to use it.
    """

    __slots__ = (
        "_process",
        "_executable_path",
    )

    def __init__(self) -> None:
        """
        Build the process manager without launching Ollama.
        """
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._executable_path: str = ""

    def detect_executable(self) -> str:
        """
        Detect an installed Ollama executable without relying on PATH.

        :returns: Absolute executable path or an empty string.
        """
        operating_system: str = platform.system()
        candidate_paths: list[str] = list()

        # Probe fixed installer locations first so detection does not depend on PATH.
        if operating_system == "Windows":
            candidate_paths.append(r"C:\Program Files\Ollama\ollama.exe")
            candidate_paths.append(r"C:\Program Files (x86)\Ollama\ollama.exe")
            candidate_paths.append(os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe"))
            candidate_paths.append(os.path.expanduser(r"~\AppData\Local\Ollama\ollama.exe"))
        else:
            if operating_system == "Darwin":
                candidate_paths.append("/opt/homebrew/bin/ollama")
                candidate_paths.append("/usr/local/bin/ollama")
                candidate_paths.append("/Applications/Ollama.app/Contents/Resources/ollama")
                candidate_paths.append(os.path.expanduser("~/Applications/Ollama.app/Contents/Resources/ollama"))
            else:
                candidate_paths.append("/usr/bin/ollama")
                candidate_paths.append("/usr/local/bin/ollama")
                candidate_paths.append("/opt/ollama/ollama")
                candidate_paths.append(os.path.expanduser("~/.local/bin/ollama"))

        index: int = 0
        while index < len(candidate_paths):
            candidate_path: str = candidate_paths[index]
            if os.path.isfile(candidate_path) and os.access(candidate_path, os.X_OK):
                self._executable_path = candidate_path
                return candidate_path
            else:
                pass
            index += 1

        self._executable_path = ""
        return ""

    def is_server_running(self, base_url: str, timeout_s: float = 0.3) -> bool:
        """
        Check whether the configured Ollama endpoint is already serving requests.

        :param base_url: OpenAI-compatible Ollama base URL.
        :param timeout_s: Probe timeout in seconds.
        :returns: True when the endpoint responds.
        """
        root_url: str = base_url.rstrip("/")

        if root_url.endswith("/v1"):
            root_url = root_url[:-3]
        else:
            pass

        try:
            with urllib.request.urlopen(f"{root_url}/api/version", timeout=timeout_s) as response:
                return int(response.status) < 500
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            return False

    def start_if_configured(self, enabled: bool, base_url: str) -> bool:
        """
        Start Ollama when it is enabled by the current AI configuration.

        :param enabled: Whether the active AI provider is Ollama.
        :param base_url: OpenAI-compatible Ollama base URL.
        :returns: True when Ollama is already running or was launched.
        """
        executable_path: str

        if enabled:
            if self.is_server_running(base_url=base_url):
                return True
            else:
                pass

            executable_path = self.detect_executable()
            if len(executable_path) == 0:
                return False
            else:
                pass

            if self._process is None:
                try:
                    self._process = subprocess.Popen(
                        [executable_path, "serve"],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return self.wait_until_running(base_url=base_url, timeout_s=8.0)
                except OSError:
                    self._process = None
                    return False
            else:
                if self._process.poll() is None:
                    return self.wait_until_running(base_url=base_url, timeout_s=8.0)
                else:
                    self._process = None
                    try:
                        self._process = subprocess.Popen(
                            [executable_path, "serve"],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        return self.wait_until_running(base_url=base_url, timeout_s=8.0)
                    except OSError:
                        self._process = None
                        return False
        else:
            return False

    def wait_until_running(self, base_url: str, timeout_s: float) -> bool:
        """
        Wait briefly until the Ollama HTTP endpoint is ready after process launch.

        :param base_url: OpenAI-compatible Ollama base URL.
        :param timeout_s: Maximum wait time in seconds.
        :returns: True when the endpoint becomes reachable.
        """
        start_time: float = time.monotonic()
        is_running: bool = self.is_server_running(base_url=base_url, timeout_s=0.5)

        while (not is_running) and ((time.monotonic() - start_time) < timeout_s):
            time.sleep(0.2)
            is_running = self.is_server_running(base_url=base_url, timeout_s=0.5)

        return is_running

    def stop(self) -> None:
        """
        Stop the Ollama process launched by VeraGrid, if any.

        :returns: Nothing.
        """
        process: Optional[subprocess.Popen[bytes]] = self._process

        if process is None:
            pass
        else:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1.0)
            else:
                pass

        self._process = None
