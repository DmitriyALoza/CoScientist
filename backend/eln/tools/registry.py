"""Tool registry for dynamic tool selection and discovery."""

from langchain_core.tools import BaseTool


class ToolRegistry:
    """Registry for managing and discovering available tools by task type."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._task_map: dict[str, list[str]] = {}  # task_type → list of tool names

    def register(self, tool: BaseTool, task_types: list[str] | None = None) -> None:
        """Register a tool, optionally associating it with task types."""
        self._tools[tool.name] = tool
        for task in (task_types or []):
            self._task_map.setdefault(task, [])
            if tool.name not in self._task_map[task]:
                self._task_map[task].append(tool.name)

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_tools_for_task(self, task_type: str) -> list[BaseTool]:
        """Return tools registered for a given task type."""
        names = self._task_map.get(task_type, [])
        return [self._tools[n] for n in names if n in self._tools]

    def all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def summary(self) -> str:
        lines = [f"Registry: {len(self._tools)} tools"]
        for task, names in self._task_map.items():
            lines.append(f"  {task}: {', '.join(names)}")
        return "\n".join(lines)
