"""OmniRun toolkit for LangChain agents."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from langchain_omnirun.tools import OmniRunFilesTool, OmniRunSandboxTool, OmniRunShellTool


class OmniRunToolkit:
    """Complete toolkit for code execution in OmniRun sandboxes.

    Provides three tools that share a single sandbox instance:
    - omnirun_execute: run Python code
    - omnirun_files: read/write files
    - omnirun_shell: run shell commands
    """

    def __init__(self, template: str = "python-3.11", timeout: int = 30) -> None:
        self.sandbox_tool = OmniRunSandboxTool(template=template, timeout=timeout)

    def get_tools(self) -> list[BaseTool]:
        """Return all OmniRun tools sharing the same sandbox."""
        return [
            self.sandbox_tool,
            OmniRunFilesTool(sandbox_tool=self.sandbox_tool),
            OmniRunShellTool(sandbox_tool=self.sandbox_tool),
        ]

    def cleanup(self) -> None:
        """Kill the sandbox and release resources."""
        self.sandbox_tool.cleanup()
