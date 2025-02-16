# SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union

from haystack_experimental.dataclasses import ByteStream


class ChatRole(str, Enum):
    """
    Enumeration representing the roles within a chat.
    """

    #: The user role. A message from the user contains only text.
    USER = "user"

    #: The system role. A message from the system contains only text.
    SYSTEM = "system"

    #: The assistant role. A message from the assistant can contain text and Tool calls. It can also store metadata.
    ASSISTANT = "assistant"

    #: The tool role. A message from a tool contains the result of a Tool invocation.
    TOOL = "tool"


@dataclass
class ToolCall:
    """
    Represents a Tool call prepared by the model, usually contained in an assistant message.

    :param id: The ID of the Tool call.
    :param tool_name: The name of the Tool to call.
    :param arguments: The arguments to call the Tool with.
    """

    tool_name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None  # noqa: A003


@dataclass
class ToolCallResult:
    """
    Represents the result of a Tool invocation.

    :param result: The result of the Tool invocation.
    :param origin: The Tool call that produced this result.
    :param error: Whether the Tool invocation resulted in an error.
    """

    result: str
    origin: ToolCall
    error: bool


@dataclass
class TextContent:
    """
    The textual content of a chat message.

    :param text: The text content of the message.
    """

    text: str


@dataclass
class MediaContent:
    """
    The media content of a chat message.

    :param media: The media content of the message.
    """

    media: ByteStream


ChatMessageContentT = Union[TextContent, MediaContent, ToolCall, ToolCallResult]


@dataclass
class ChatMessage:
    """
    Represents a message in a LLM chat conversation.

    :param content: The content of the message.
    :param role: The role of the entity sending the message.
    :param meta: Additional metadata associated with the message.
    """

    _role: ChatRole
    _content: Sequence[ChatMessageContentT]
    _meta: Dict[str, Any] = field(default_factory=dict, hash=False)
    _name: Optional[str] = None

    def __len__(self):
        return len(self._content)

    @property
    def name(self) -> Optional[str]:
        """
        Returns the name for the message participant, if provided.

        """
        return self._name

    @property
    def content(self) -> Sequence[ChatMessageContentT]:
        """
        Returns the content of the message.
        """
        return self._content

    @property
    def role(self) -> ChatRole:
        """
        Returns the role of the entity sending the message.
        """
        return self._role

    @property
    def meta(self) -> Dict[str, Any]:
        """
        Returns the metadata associated with the message.
        """
        return self._meta

    @property
    def texts(self) -> List[str]:
        """
        Returns the list of all texts contained in the message.
        """
        return [content.text for content in self._content if isinstance(content, TextContent)]

    @property
    def text(self) -> Optional[str]:
        """
        Returns the first text contained in the message.
        """
        if texts := self.texts:
            return texts[0]
        return None

    @property
    def media(self) -> List[ByteStream]:
        """
        Returns the list of all media content contained in the message.

        :return: List of ByteStream objects.
        """
        return [content.media for content in self._content if isinstance(content, MediaContent)]

    @property
    def tool_calls(self) -> List[ToolCall]:
        """
        Returns the list of all Tool calls contained in the message.
        """
        return [content for content in self._content if isinstance(content, ToolCall)]

    @property
    def tool_call(self) -> Optional[ToolCall]:
        """
        Returns the first Tool call contained in the message.
        """
        if tool_calls := self.tool_calls:
            return tool_calls[0]
        return None

    @property
    def tool_call_results(self) -> List[ToolCallResult]:
        """
        Returns the list of all Tool call results contained in the message.
        """
        return [content for content in self._content if isinstance(content, ToolCallResult)]

    @property
    def tool_call_result(self) -> Optional[ToolCallResult]:
        """
        Returns the first Tool call result contained in the message.
        """
        if tool_call_results := self.tool_call_results:
            return tool_call_results[0]
        return None

    def is_from(self, role: ChatRole) -> bool:
        """
        Check if the message is from a specific role.

        :param role: The role to check against.
        :returns: True if the message is from the specified role, False otherwise.
        """
        return self._role == role

    @classmethod
    def from_user(
        cls,
        text: str,
        media: Optional[Sequence[ByteStream]] = None,
        name: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "ChatMessage":
        """
        Create a message from the user.

        :param text: The text content of the message.
        :param media: The media contents of the message, if any.
        :param name: An optional name for the message participant.
        :param meta: Additional metadata associated with the message.
        :returns: A new ChatMessage instance.
        """
        media_contents = [MediaContent(media=media) for media in media] if media else []
        return cls(
            _role=ChatRole.USER, _content=[TextContent(text=text), *media_contents], _name=name, _meta=meta or {}
        )

    @classmethod
    def from_system(
        cls,
        text: str,
        name: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "ChatMessage":
        """
        Create a message from the system.

        :param text: The text content of the message.
        :param name: An optional name for the message participant.
        :param meta: Additional metadata associated with the message.
        :returns: A new ChatMessage instance.
        """
        return cls(_role=ChatRole.SYSTEM, _content=[TextContent(text=text)], _name=name, _meta=meta or {})

    @classmethod
    def from_assistant(
        cls,
        text: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None,
        name: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "ChatMessage":
        """
        Create a message from the assistant.

        :param text: The text content of the message.
        :param tool_calls: The Tool calls to include in the message.
        :param name: An optional name for the message participant.
        :param meta: Additional metadata associated with the message.
        :returns: A new ChatMessage instance.
        """
        content: List[ChatMessageContentT] = []
        if text is not None:
            content.append(TextContent(text=text))
        if tool_calls:
            content.extend(tool_calls)

        return cls(_role=ChatRole.ASSISTANT, _content=content, _name=name, _meta=meta or {})

    @classmethod
    def from_tool(
        cls,
        tool_result: str,
        origin: ToolCall,
        error: bool = False,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "ChatMessage":
        """
        Create a message from a Tool.

        :param tool_result: The result of the Tool invocation.
        :param origin: The Tool call that produced this result.
        :param error: Whether the Tool invocation resulted in an error.
        :param meta: Additional metadata associated with the message.
        :returns: A new ChatMessage instance.
        """
        return cls(
            _role=ChatRole.TOOL,
            _content=[ToolCallResult(result=tool_result, origin=origin, error=error)],
            _meta=meta or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts ChatMessage into a dictionary.

        :returns:
            Serialized version of the object.
        """
        serialized: Dict[str, Any] = {"_role": self._role.value, "_name": self._name, "_meta": self._meta}

        content: List[Dict[str, Any]] = []
        for part in self._content:
            if isinstance(part, TextContent):
                content.append({"text": part.text})
            elif isinstance(part, MediaContent):
                content.append({"media": part.media.to_dict()})
            elif isinstance(part, ToolCall):
                content.append({"tool_call": asdict(part)})
            elif isinstance(part, ToolCallResult):
                content.append({"tool_call_result": asdict(part)})
            else:
                raise TypeError(f"Unsupported type in ChatMessage content: `{type(part).__name__}` for `{part}`.")

        serialized["_content"] = content
        return serialized

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """
        Creates a new ChatMessage object from a dictionary.

        :param data:
            The dictionary to build the ChatMessage object.
        :returns:
            The created object.
        """
        data["_role"] = ChatRole(data["_role"])

        content: List[ChatMessageContentT] = []

        for part in data["_content"]:
            if "text" in part:
                content.append(TextContent(text=part["text"]))
            elif "media" in part:
                content.append(MediaContent(media=ByteStream.from_dict(part["media"])))
            elif "tool_call" in part:
                content.append(ToolCall(**part["tool_call"]))
            elif "tool_call_result" in part:
                result = part["tool_call_result"]["result"]
                origin = ToolCall(**part["tool_call_result"]["origin"])
                error = part["tool_call_result"]["error"]
                tcr = ToolCallResult(result=result, origin=origin, error=error)
                content.append(tcr)
            else:
                raise ValueError(f"Unsupported content in serialized ChatMessage: `{part}`")

        data["_content"] = content

        return cls(**data)
    
    def to_openai_dict_format(self) -> Dict[str, Any]:
        """
        Convert a ChatMessage to the dictionary format expected by OpenAI's Chat API.
        """
        text_contents = self.texts
        tool_calls = self.tool_calls
        tool_call_results = self.tool_call_results

        if not text_contents and not tool_calls and not tool_call_results:
            raise ValueError(
                "A `ChatMessage` must contain at least one `TextContent`, `ToolCall`, or `ToolCallResult`."
            )
        if len(text_contents) + len(tool_call_results) > 1:
            raise ValueError("A `ChatMessage` can only contain one `TextContent` or one `ToolCallResult`.")

        openai_msg: Dict[str, Any] = {"role": self._role.value}

        if tool_call_results:
            result = tool_call_results[0]
            if result.origin.id is None:
                raise ValueError("`ToolCall` must have a non-null `id` attribute to be used with OpenAI.")
            openai_msg["content"] = result.result
            openai_msg["tool_call_id"] = result.origin.id
            # OpenAI does not provide a way to communicate errors in tool invocations, so we ignore the error field
            return openai_msg

        if text_contents:
            openai_msg["content"] = text_contents[0]
        if tool_calls:
            openai_tool_calls = []
            for tc in tool_calls:
                if tc.id is None:
                    raise ValueError("`ToolCall` must have a non-null `id` attribute to be used with OpenAI.")
                openai_tool_calls.append(
                    {
                        "id": tc.id,
                        "type": "function",
                        # We disable ensure_ascii so special chars like emojis are not converted
                        "function": {"name": tc.tool_name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    }
                )
            openai_msg["tool_calls"] = openai_tool_calls
        return openai_msg

    @staticmethod
    def _validate_openai_message(message: Dict[str, Any]) -> None:
        """
        Validate that a message dictionary follows OpenAI's Chat API format.

        :param message: The message dictionary to validate
        :raises ValueError: If the message format is invalid
        """
        if "role" not in message:
            raise ValueError("The `role` field is required in the message dictionary.")

        role = message["role"]
        content = message.get("content")
        tool_calls = message.get("tool_calls")

        if role not in ["assistant", "user", "system", "developer", "tool"]:
            raise ValueError(f"Unsupported role: {role}")

        if role == "assistant":
            if not content and not tool_calls:
                raise ValueError("For assistant messages, either `content` or `tool_calls` must be present.")
            if tool_calls:
                for tc in tool_calls:
                    if "function" not in tc:
                        raise ValueError("Tool calls must contain the `function` field")
        elif not content:
            raise ValueError(f"The `content` field is required for {role} messages.")

    @classmethod
    def from_openai_dict_format(cls, message: Dict[str, Any]) -> "ChatMessage":
        """
        Create a ChatMessage from a dictionary in the format expected by OpenAI's Chat API.

        NOTE: While OpenAI's API requires `tool_call_id` in both tool calls and tool messages, this method
        accepts messages without it to support shallow OpenAI-compatible APIs.
        If you plan to use the resulting ChatMessage with OpenAI, you must include `tool_call_id` or you'll
        encounter validation errors.

        :param message:
            The OpenAI dictionary to build the ChatMessage object.
        :returns:
            The created ChatMessage object.

        :raises ValueError:
            If the message dictionary is missing required fields.
        """
        cls._validate_openai_message(message)

        role = message["role"]
        content = message.get("content")
        name = message.get("name")
        tool_calls = message.get("tool_calls")
        tool_call_id = message.get("tool_call_id")

        if role == "assistant":
            haystack_tool_calls = None
            if tool_calls:
                haystack_tool_calls = []
                for tc in tool_calls:
                    haystack_tc = ToolCall(
                        id=tc.get("id"),
                        tool_name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]),
                    )
                    haystack_tool_calls.append(haystack_tc)
            return cls.from_assistant(text=content, name=name, tool_calls=haystack_tool_calls)

        assert content is not None  # ensured by _validate_openai_message, but we need to make mypy happy

        if role == "user":
            return cls.from_user(text=content, name=name)
        if role in ["system", "developer"]:
            return cls.from_system(text=content, name=name)

        return cls.from_tool(
            tool_result=content, origin=ToolCall(id=tool_call_id, tool_name="", arguments={}), error=False
        )