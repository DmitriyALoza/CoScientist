from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from langchain_core.language_models import BaseChatModel

from eln.models.citation import Citation


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[dict] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None
    model: str = ""
    provider: str = ""


class BaseProvider(ABC):
    """
    Provider-agnostic interface for LLM access.

    Exposes:
      - `llm`: the underlying LangChain chat model
        (for use with create_react_agent / create_supervisor)
      - `chat()`: direct async call returning LLMResponse (for use outside of LangGraph)
    """

    @property
    @abstractmethod
    def llm(self) -> BaseChatModel:
        """The configured LangChain chat model instance."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name, e.g. 'anthropic'."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier string."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list | None = None,
        response_format: dict | type | None = None,
        stream: bool = True,
    ) -> LLMResponse:
        """
        Low-level chat call. `messages` is a list of {'role': ..., 'content': ...} dicts.
        Returns a fully-collected LLMResponse (even in stream mode the result is buffered).
        """
