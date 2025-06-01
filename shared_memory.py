from datetime import datetime
from typing import Dict, Any, Optional
import json
import redis

class SharedMemory:
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        print("\n🔧 Initialized SharedMemory system (Redis-backed)")

    def _context_key(self, conversation_id: str) -> str:
        return f"context:{conversation_id}"

    def _logs_key(self, conversation_id: str) -> str:
        return f"logs:{conversation_id}"

    def _print_memory_state(self, operation: str, conversation_id: str) -> None:
        """Print current memory state for traceability"""
        print(f"\n📝 Memory Operation: {operation}")
        print(f"🔑 Conversation ID: {conversation_id}")
        
        context = self.get_context(conversation_id)
        if context:
            print("\n📋 Current Context:")
            for key, value in context.items():
                print(f"  - {key}: {value}")
        
        history = self.get_processing_history(conversation_id)
        if history:
            print("\n📜 Processing Logs:")
            for log_entry in history:
                log_entry = json.loads(log_entry)
                print(f"  - {log_entry['timestamp']} | {log_entry['agent']} | {log_entry['action']}")
                if 'details' in log_entry:
                    print(f"    Details: {json.dumps(log_entry['details'], indent=2)}")

    def store_context(self, conversation_id: str, data: Dict[str, Any]) -> None:
        """Store context for a conversation"""
        data['timestamp'] = datetime.utcnow().isoformat()
        self.redis.set(self._context_key(conversation_id), json.dumps(data))
        self._print_memory_state("Store Context", conversation_id)

    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve context for a conversation"""
        context_json = self.redis.get(self._context_key(conversation_id))
        print(f"\n🔍 Retrieved context for conversation {conversation_id}")
        if context_json:
            context = json.loads(context_json)
            print(f"  Found {len(context)} context items")
            return context
        else:
            print("  No context found")
            return None

    def update_context(self, conversation_id: str, updates: Dict[str, Any]) -> None:
        """Update existing context with new information"""
        print(f"\n📝 Updating context for conversation {conversation_id}")
        print(f"  Updates to apply: {json.dumps(updates, indent=2)}")
        
        context = self.get_context(conversation_id) or {}
        old_context = dict(context)
        context.update(updates)
        self.redis.set(self._context_key(conversation_id), json.dumps(context))
        
        print("\n  Changes made:")
        for key, new_value in updates.items():
            old_value = old_context.get(key, 'NOT_SET')
            print(f"  - {key}: {old_value} -> {new_value}")
        self._print_memory_state("Update Context", conversation_id)

    def log_processing(self, conversation_id: str, agent: str, action: str, details: Dict[str, Any]) -> None:
        """Log processing steps for traceability"""
        print(f"\n📌 Logging processing step:")
        print(f"  Agent: {agent}")
        print(f"  Action: {action}")
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent': agent,
            'action': action,
            'details': details
        }
        self.redis.rpush(self._logs_key(conversation_id), json.dumps(log_entry))
        print(f"  Added log entry #{self.redis.llen(self._logs_key(conversation_id))}")
        
        self._print_memory_state("Log Processing", conversation_id)

    def get_processing_history(self, conversation_id: str) -> list:
        """Retrieve processing history for a conversation"""
        history = self.redis.lrange(self._logs_key(conversation_id), 0, -1)
        print(f"\n📜 Retrieved processing history for conversation {conversation_id}")
        print(f"  Found {len(history)} log entries")
        return history

    def clear_context(self, conversation_id: str) -> None:
        """Clear all data for a conversation"""
        print(f"\n🗑️ Clearing data for conversation {conversation_id}")
        
        self.redis.delete(self._context_key(conversation_id))
        self.redis.delete(self._logs_key(conversation_id))
            
        print("  Cleanup complete") 