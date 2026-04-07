"""OmniRun sandbox tools for LangChain."""

from __future__ import annotations

import shlex
from typing import Any

from langchain_core.tools import BaseTool
from omnirun import Sandbox
from pydantic import BaseModel, Field, PrivateAttr


class CodeInput(BaseModel):
    """Input schema for code execution."""

    code: str = Field(description="Python code to execute in the sandbox")


class OmniRunSandboxTool(BaseTool):
    """Execute Python code in an isolated Firecracker microVM sandbox."""

    name: str = "omnirun_execute"
    description: str = (
        "Execute Python code in an isolated Firecracker microVM sandbox. "
        "Each execution gets its own Linux kernel with hardware-level isolation. "
        "Returns stdout, stderr, and exit code."
    )
    args_schema: type = CodeInput

    template: str = "python-3.11"
    timeout: int = 30

    _sandbox: Sandbox | None = PrivateAttr(default=None)

    def _get_sandbox(self) -> Sandbox:
        if self._sandbox is None:
            self._sandbox = Sandbox.create(self.template, timeout=300)
        return self._sandbox

    def _run(self, code: str, **kwargs: Any) -> str:
        sb = self._get_sandbox()
        result = sb.commands.run(
            f"python3 -c {shlex.quote(code)}", timeout=self.timeout
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        if result.exit_code != 0:
            output += f"\nExit code: {result.exit_code}"
        return output or "(no output)"

    def cleanup(self) -> None:
        """Kill the sandbox and release resources."""
        if self._sandbox is not None:
            self._sandbox.kill()
            self._sandbox = None


class FileInput(BaseModel):
    """Input schema for file operations."""

    action: str = Field(description="Action: 'read' or 'write'")
    path: str = Field(description="File path in the sandbox")
    content: str = Field(default="", description="File content (for write)")


class OmniRunFilesTool(BaseTool):
    """Read or write files in the OmniRun sandbox."""

    name: str = "omnirun_files"
    description: str = (
        "Read or write files in the OmniRun sandbox. "
        "Use action='write' with path and content, or action='read' with just path."
    )
    args_schema: type = FileInput

    sandbox_tool: OmniRunSandboxTool

    def _run(self, action: str, path: str, content: str = "", **kwargs: Any) -> str:
        sb = self.sandbox_tool._get_sandbox()
        if action == "write":
            sb.files.write(path, content)
            return f"Written {len(content)} bytes to {path}"
        elif action == "read":
            return sb.files.read(path)
        return f"Unknown action: {action}"


class ShellInput(BaseModel):
    """Input schema for shell commands."""

    command: str = Field(description="Shell command to run")


class OmniRunShellTool(BaseTool):
    """Run a shell command in the OmniRun sandbox."""

    name: str = "omnirun_shell"
    description: str = (
        "Run a shell command in the sandbox "
        "(e.g. install packages with pip, list files, etc.)"
    )
    args_schema: type = ShellInput

    sandbox_tool: OmniRunSandboxTool

    def _run(self, command: str, **kwargs: Any) -> str:
        sb = self.sandbox_tool._get_sandbox()
        result = sb.commands.run(command, timeout=60)
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        if result.exit_code != 0:
            output += f"\nExit code: {result.exit_code}"
        return output or "(no output)"
