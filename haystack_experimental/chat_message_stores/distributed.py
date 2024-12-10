# SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
#
# SPDX-License-Identifier: Apache-2.0

from haystack import Document

from typing import Any, Dict, Iterable, List

from haystack import default_from_dict, default_to_dict, logging
from haystack.dataclasses import ChatMessage

from haystack_experimental.chat_message_stores.types import ChatMessageStore

logger = logging.getLogger(__name__)


class DistributedChatMessageStore(ChatMessageStore):
    """
    Stores chat messages in-memory.
    """

    def __init__(
        self,
        document_store=None
    ):
        """
        Initializes the InMemoryChatMessageStore.
        """
        self.messages = []
        self.document_store=document_store

    @staticmethod
    def to_document(chat_message: ChatMessage) -> Document:
        """
        Converts a ChatMessage to a Document.

        :param chat_message:
            The ChatMessage to convert.
        :returns:
            The Document.
        """
        return Document(
            content=chat_message.content,
            meta=chat_message.meta,
        )


    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the component to a dictionary.

        :returns:
            Dictionary with serialized data.
        """
        return default_to_dict(
            self,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DistibutedChatMessageStore":
        """
        Deserializes the component from a dictionary.

        :param data:
            The dictionary to deserialize from.
        :returns:
            The deserialized component.
        """
        return default_from_dict(cls, data)

    def count_messages(self) -> int:
        """
        Returns the number of chat messages stored.

        :returns: The number of messages.
        """
        return len(self.messages)

    def write_messages(self, messages: List[ChatMessage]) -> int:
        """
        Writes chat messages to the ChatMessageStore.

        :param messages: A list of ChatMessages to write.
        :returns: The number of messages written.

        :raises ValueError: If messages is not a list of ChatMessages.
        """
        if not isinstance(messages, Iterable) or any(not isinstance(message, ChatMessage) for message in messages):
            raise ValueError("Please provide a list of ChatMessages.")
        
        print([self.to_document(message) for message in messages])

        self.messages.extend(messages)
        return len(messages)

    def delete_messages(self) -> None:
        """
        Deletes all stored chat messages.
        """
        self.messages = []

    def retrieve(self) -> List[ChatMessage]:
        """
        Retrieves all stored chat messages.

        :returns: A list of chat messages.
        """
        return self.messages
