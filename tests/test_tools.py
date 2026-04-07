"""Unit tests for langchain-omnirun tools (mocked, no API keys needed)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langchain_omnirun import OmniRunFilesTool, OmniRunSandboxTool, OmniRunShellTool, OmniRunToolkit


class TestOmniRunSandboxTool:
    def test_name_and_description(self):
        tool = OmniRunSandboxTool()
        assert tool.name == "omnirun_execute"
        assert "Firecracker" in tool.description

    def test_default_template(self):
        tool = OmniRunSandboxTool()
        assert tool.template == "python-3.11"

    def test_custom_template(self):
        tool = OmniRunSandboxTool(template="node-20", timeout=60)
        assert tool.template == "node-20"
        assert tool.timeout == 60

    def test_input_schema(self):
        tool = OmniRunSandboxTool()
        schema = tool.args_schema.model_json_schema()
        assert "code" in schema["properties"]

    @patch("langchain_omnirun.tools.Sandbox")
    def test_run_returns_stdout(self, mock_sandbox_cls):
        mock_sb = MagicMock()
        mock_sandbox_cls.create.return_value = mock_sb
        mock_result = MagicMock()
        mock_result.stdout = "hello"
        mock_result.stderr = ""
        mock_result.exit_code = 0
        mock_sb.commands.run.return_value = mock_result

        tool = OmniRunSandboxTool()
        output = tool._run(code="print('hello')")
        assert "hello" in output

    @patch("langchain_omnirun.tools.Sandbox")
    def test_run_includes_stderr(self, mock_sandbox_cls):
        mock_sb = MagicMock()
        mock_sandbox_cls.create.return_value = mock_sb
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "traceback"
        mock_result.exit_code = 1
        mock_sb.commands.run.return_value = mock_result

        tool = OmniRunSandboxTool()
        output = tool._run(code="bad code")
        assert "STDERR: traceback" in output
        assert "Exit code: 1" in output

    @patch("langchain_omnirun.tools.Sandbox")
    def test_cleanup(self, mock_sandbox_cls):
        mock_sb = MagicMock()
        mock_sandbox_cls.create.return_value = mock_sb

        tool = OmniRunSandboxTool()
        tool._get_sandbox()
        tool.cleanup()
        mock_sb.kill.assert_called_once()


class TestOmniRunFilesTool:
    def test_name_and_description(self):
        sandbox_tool = OmniRunSandboxTool()
        tool = OmniRunFilesTool(sandbox_tool=sandbox_tool)
        assert tool.name == "omnirun_files"
        assert "Read or write" in tool.description

    def test_input_schema(self):
        sandbox_tool = OmniRunSandboxTool()
        tool = OmniRunFilesTool(sandbox_tool=sandbox_tool)
        schema = tool.args_schema.model_json_schema()
        assert "action" in schema["properties"]
        assert "path" in schema["properties"]
        assert "content" in schema["properties"]

    @patch("langchain_omnirun.tools.Sandbox")
    def test_write_file(self, mock_sandbox_cls):
        mock_sb = MagicMock()
        mock_sandbox_cls.create.return_value = mock_sb

        sandbox_tool = OmniRunSandboxTool()
        tool = OmniRunFilesTool(sandbox_tool=sandbox_tool)
        result = tool._run(action="write", path="/tmp/test.py", content="x = 1")
        assert "Written 5 bytes" in result
        mock_sb.files.write.assert_called_once_with("/tmp/test.py", "x = 1")

    @patch("langchain_omnirun.tools.Sandbox")
    def test_read_file(self, mock_sandbox_cls):
        mock_sb = MagicMock()
        mock_sandbox_cls.create.return_value = mock_sb
        mock_sb.files.read.return_value = "file contents"

        sandbox_tool = OmniRunSandboxTool()
        tool = OmniRunFilesTool(sandbox_tool=sandbox_tool)
        result = tool._run(action="read", path="/tmp/test.py")
        assert result == "file contents"

    def test_unknown_action(self):
        sandbox_tool = OmniRunSandboxTool()
        tool = OmniRunFilesTool(sandbox_tool=sandbox_tool)
        with patch("langchain_omnirun.tools.Sandbox"):
            result = tool._run(action="delete", path="/tmp/test.py")
        assert "Unknown action" in result


class TestOmniRunShellTool:
    def test_name_and_description(self):
        sandbox_tool = OmniRunSandboxTool()
        tool = OmniRunShellTool(sandbox_tool=sandbox_tool)
        assert tool.name == "omnirun_shell"
        assert "shell command" in tool.description

    def test_input_schema(self):
        sandbox_tool = OmniRunSandboxTool()
        tool = OmniRunShellTool(sandbox_tool=sandbox_tool)
        schema = tool.args_schema.model_json_schema()
        assert "command" in schema["properties"]


class TestOmniRunToolkit:
    def test_get_tools_returns_three(self):
        toolkit = OmniRunToolkit()
        tools = toolkit.get_tools()
        assert len(tools) == 3
        names = {t.name for t in tools}
        assert names == {"omnirun_execute", "omnirun_files", "omnirun_shell"}

    def test_tools_share_sandbox(self):
        toolkit = OmniRunToolkit()
        tools = toolkit.get_tools()
        sandbox_tool = tools[0]
        files_tool = tools[1]
        shell_tool = tools[2]
        assert files_tool.sandbox_tool is sandbox_tool
        assert shell_tool.sandbox_tool is sandbox_tool

    @patch("langchain_omnirun.tools.Sandbox")
    def test_cleanup(self, mock_sandbox_cls):
        mock_sb = MagicMock()
        mock_sandbox_cls.create.return_value = mock_sb

        toolkit = OmniRunToolkit()
        toolkit.sandbox_tool._get_sandbox()
        toolkit.cleanup()
        mock_sb.kill.assert_called_once()
