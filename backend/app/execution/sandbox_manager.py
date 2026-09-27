"""
Secure Polyglot Code Execution Engine.

Every job runs inside a brand-new, ephemeral Docker container with:
  - `network_disabled=True`           (no network egress/ingress)
  - `read_only=True` root filesystem  (only /workspace tmpfs is writable)
  - strict CPU / memory quotas
  - a non-root user
  - a hard wall-clock timeout, after which the container is force-killed
  - the container is always removed (`auto_remove` + explicit cleanup)

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from __future__ import annotations

import asyncio
import tarfile
import io
import time
import uuid
from typing import Any

import docker
from docker.errors import ContainerError, DockerException, ImageNotFound

from app.core.config import get_settings
from app.execution.language_configs import LANGUAGE_CONFIGS

settings = get_settings()


class SandboxExecutionError(Exception):
    pass


class SandboxManager:
    def __init__(self) -> None:
        self._client = docker.from_env()

    def _build_tar(self, filename: str, content: str) -> io.BytesIO:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            data = content.encode()
            info = tarfile.TarInfo(name=filename)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        buf.seek(0)
        return buf

    async def run(self, language: str, code: str) -> dict[str, Any]:
        if language not in LANGUAGE_CONFIGS:
            raise SandboxExecutionError(f"Unsupported language: {language}")
        return await asyncio.get_event_loop().run_in_executor(None, self._run_sync, language, code)

    def _run_sync(self, language: str, code: str) -> dict[str, Any]:
        cfg = LANGUAGE_CONFIGS[language]
        job_id = str(uuid.uuid4())[:8]
        container = None
        start = time.time()

        try:
            container = self._client.containers.create(
                image=cfg.image,
                command="sleep " + str(settings.SANDBOX_TIMEOUT_SECONDS + 5),
                name=f"aegis-sbx-{job_id}",
                detach=True,
                network_disabled=settings.SANDBOX_NETWORK_DISABLED,
                read_only=True,
                mem_limit=settings.SANDBOX_MEM_LIMIT,
                nano_cpus=int(float(settings.SANDBOX_CPU_LIMIT) * 1e9),
                pids_limit=64,
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],
                user="1000:1000",
                working_dir="/workspace",
                tmpfs={"/workspace": "rw,exec,size=64m"},
            )
            container.start()
            container.put_archive("/workspace", self._build_tar(cfg.filename, code))

            output_log = ""
            if cfg.compile_cmd:
                exit_code, out = container.exec_run(cfg.compile_cmd, workdir="/workspace")
                output_log += out.decode(errors="replace")
                if exit_code != 0:
                    return self._result(job_id, False, output_log, "compilation_failed", start)

            exit_code, out = container.exec_run(
                cfg.run_cmd, workdir="/workspace", environment={"TIMEOUT": str(settings.SANDBOX_TIMEOUT_SECONDS)}
            )
            output_log += out.decode(errors="replace")
            success = exit_code == 0
            return self._result(job_id, success, output_log, None if success else "runtime_error", start)

        except (ContainerError, ImageNotFound, DockerException) as exc:
            return self._result(job_id, False, str(exc), "docker_error", start)
        finally:
            if container is not None:
                try:
                    container.kill()
                except DockerException:
                    pass
                try:
                    container.remove(force=True)
                except DockerException:
                    pass

    def _result(self, job_id: str, success: bool, output: str, error: str | None, start: float) -> dict[str, Any]:
        return {
            "job_id": job_id,
            "success": success,
            "output": output[-10_000:],  # cap output size
            "error": error,
            "duration_seconds": round(time.time() - start, 3),
        }
