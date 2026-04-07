"""Example: LangChain agent with OmniRun sandbox tools.

Requires: OMNIRUN_API_KEY and OPENAI_API_KEY environment variables.

Usage:
    python examples/agent_example.py
"""

from langchain_omnirun import OmniRunToolkit

toolkit = OmniRunToolkit()
tools = toolkit.get_tools()

# Show available tools
print("Available tools:")
for tool in tools:
    print(f"  - {tool.name}: {tool.description[:60]}...")

# Direct tool usage example
print("\nExecuting code in sandbox...")
result = tools[0].invoke({"code": "print('Hello from Firecracker!')"})
print(f"Result: {result}")

# File operations
print("\nWriting a file...")
tools[1].invoke({"action": "write", "path": "/tmp/data.txt", "content": "sample data"})

print("Reading the file back...")
content = tools[1].invoke({"action": "read", "path": "/tmp/data.txt"})
print(f"Content: {content}")

# Shell command
print("\nRunning shell command...")
result = tools[2].invoke({"command": "uname -a"})
print(f"System info: {result}")

toolkit.cleanup()
print("\nDone.")
