"""Communication Fabric — NATS-inspired message bus for inter-agent communication."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import json
import queue
import threading
import uuid


class MessageType(str, Enum):
    TASK_REQUEST = "task-request"
    TASK_RESPONSE = "task-response"
    REVIEW_REQUEST = "review-request"
    REVIEW_RESPONSE = "review-response"
    STATUS_UPDATE = "status-update"
    ERROR = "error"
    LEARNING = "learning"
    GUILD_MESSAGE = "guild-message"
    INSTITUTION_MESSAGE = "institution-message"
    TEAM_FORMATION = "team-formation"
    REPUTATION_UPDATE = "reputation-update"


class MessagePriority(int, Enum):
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str = ""
    recipient: str = ""
    type: MessageType = MessageType.STATUS_UPDATE
    payload: dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str | None = None
    subject: str = ""  # NATS-style subject

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.type.value,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "subject": self.subject,
        }


class MessageBus:
    """Thread-safe pub/sub message bus with NATS-style subjects."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Message], None]]] = {}
        self._queue: queue.PriorityQueue[tuple[int, int, Message]] = queue.PriorityQueue()
        self._counter = 0
        self._lock = threading.Lock()
        self._running = False
        self._worker: threading.Thread | None = None
        self._message_log: list[Message] = []

    def subscribe(self, topic: str, handler: Callable[[Message], None]) -> None:
        with self._lock:
            self._subscribers.setdefault(topic, []).append(handler)

    def unsubscribe(self, topic: str, handler: Callable[[Message], None]) -> None:
        with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic] = [h for h in self._subscribers[topic] if h != handler]

    def publish(self, message: Message) -> None:
        with self._lock:
            self._counter += 1
            self._queue.put((message.priority.value, self._counter, message))
            self._message_log.append(message)

    def request_reply(self, message: Message, timeout: float = 30.0) -> Message | None:
        """Send a request and wait for a reply (NATS-style request-reply)."""
        reply_queue: queue.Queue[Message] = queue.Queue()
        correlation_id = str(uuid.uuid4())[:8]
        message.correlation_id = correlation_id

        def handler(msg: Message) -> None:
            if msg.correlation_id == correlation_id:
                reply_queue.put(msg)

        self.subscribe(f"reply.{correlation_id}", handler)
        self.publish(message)
        try:
            return reply_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            self.unsubscribe(f"reply.{correlation_id}", handler)

    def start(self) -> None:
        self._running = True
        self._worker = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._running = False
        if self._worker:
            self._worker.join(timeout=5)

    def get_message_log(self) -> list[Message]:
        return list(self._message_log)

    def _dispatch_loop(self) -> None:
        while self._running:
            try:
                _, _, msg = self._queue.get(timeout=0.5)
                self._dispatch(msg)
            except queue.Empty:
                continue

    def _dispatch(self, msg: Message) -> None:
        with self._lock:
            handlers = list(self._subscribers.get(msg.recipient, []))
            handlers.extend(self._subscribers.get("*", []))
            # NATS-style subject matching
            for topic in self._subscribers:
                if self._subject_match(topic, msg.subject):
                    handlers.extend(self._subscribers[topic])
        for handler in handlers:
            try:
                handler(msg)
            except Exception:
                pass

    def _subject_match(self, pattern: str, subject: str) -> bool:
        """Simple NATS-style subject matching with * and > wildcards."""
        if not pattern or not subject:
            return False
        if pattern == ">":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return subject.startswith(prefix + ".") or subject == prefix
        if pattern.endswith(".>"):
            prefix = pattern[:-2]
            return subject.startswith(prefix + ".")
        return pattern == subject
