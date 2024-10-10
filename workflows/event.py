from llama_index.core.llms import ChatMessage
from llama_index.core.tools import ToolSelection, ToolOutput
from llama_index.core.workflow import Event


class InputEvent(Event):
    input: list[ChatMessage]


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


class FunctionOutputEvent(Event):
    output: ToolOutput


class QueryEvent(Event):
    question: str


class AnswerEvent(Event):
    question: str
    answer: str


class ProcessEvent(Event):
    data: str 


class ResultEvent(Event):
    result: str
