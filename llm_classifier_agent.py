import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from base_agent import BaseAgent
from typing import Dict, Any, Union
import torch.nn.functional as F

class LLMClassifierAgent(BaseAgent):
    INTENT_LABELS = ['invoice', 'rfq', 'complaint', 'regulation', 'unknown']

    def __init__(self):
        super().__init__()
        self.model_name = 'distilbert-base-uncased-finetuned-sst-2-english'
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def process(self, data: Union[str, bytes], conversation_id: str) -> Dict[str, Any]:
        """
        Use the LLM to classify the intent of the input text.
        Returns: Dict containing format, intent, and routing decision
        """
        format_type = self._detect_format(data)
        content = self._extract_content(data, format_type)
        intent = self._classify_intent_llm(content)

        result = {
            'format': format_type,
            'intent': intent,
            'route_to': self._determine_route(format_type, intent)
        }

        # Log the classification
        self.log_action(
            conversation_id=conversation_id,
            action='classify_llm',
            details=result
        )

        # Store in context
        self.update_context(conversation_id, {
            'format': format_type,
            'intent': intent,
            'classification_timestamp': True
        })

        return result

    def _detect_format(self, data: Union[str, bytes]) -> str:
        # Same as in ClassifierAgent
        import json, email
        if isinstance(data, bytes) and data.startswith(b'%PDF'):
            return 'pdf'
        try:
            if isinstance(data, str):
                json.loads(data)
                return 'json'
        except Exception:
            pass
        try:
            if isinstance(data, str):
                email.message_from_string(data)
                return 'email'
            elif isinstance(data, bytes):
                email.message_from_bytes(data)
                return 'email'
        except:
            pass
        return 'unknown'

    def _extract_content(self, data: Union[str, bytes], format_type: str) -> str:
        # Same as in ClassifierAgent
        import json, email
        if format_type == 'pdf':
            return ''  # Not supported for now
        elif format_type == 'json':
            json_data = json.loads(data if isinstance(data, str) else data.decode())
            return str(json_data)
        elif format_type == 'email':
            if isinstance(data, bytes):
                msg = email.message_from_bytes(data)
            else:
                msg = email.message_from_string(data)
            return msg.get_payload()
        return str(data)

    def _classify_intent_llm(self, content: str) -> str:
        # Use zero-shot approach: pick the label with highest score
        prompt = f"Classify the intent of this document: {content[:512]}"
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1).cpu().numpy()[0]
        # For demonstration, map positive/negative to intents
        # (since distilbert-base-uncased-finetuned-sst-2-english is a sentiment model)
        # You can later fine-tune or swap for a true intent classifier
        if probs[1] > 0.7:
            return 'rfq'  # treat positive as 'rfq' (example)
        elif probs[0] > 0.7:
            return 'complaint'  # treat negative as 'complaint' (example)
        return 'unknown'

    def _determine_route(self, format_type: str, intent: str) -> str:
        if format_type == 'json':
            return 'json_agent'
        elif format_type == 'email':
            return 'email_agent'
        else:
            return 'email_agent' 