from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from shared_memory import SharedMemory

class BaseAgent(ABC):
    def __init__(self):
        self.memory = SharedMemory()

    @abstractmethod
    def process(self, data: Any, conversation_id: str) -> Dict[str, Any]:
        """Process the input data"""
        pass

    def log_action(self, conversation_id: str, action: str, details: Dict[str, Any]) -> None:
        """Log an action performed by the agent"""
        self.memory.log_processing(
            conversation_id=conversation_id,
            agent=self.__class__.__name__,
            action=action,
            details=details
        )

    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get context for the current conversation"""
        return self.memory.get_context(conversation_id)

    def update_context(self, conversation_id: str, updates: Dict[str, Any]) -> None:
        """Update context with new information"""
        self.memory.update_context(conversation_id, updates)

    def get_history(self, conversation_id: str) -> list:
        """Get processing history for the conversation"""
        return self.memory.get_processing_history(conversation_id) 