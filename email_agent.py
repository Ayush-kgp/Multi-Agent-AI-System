import email
from email.message import EmailMessage
from typing import Dict, Any, Optional
from base_agent import BaseAgent
from email_validator import validate_email, EmailNotValidError
import re

class EmailAgent(BaseAgent):
    URGENCY_KEYWORDS = {
        'high': ['urgent', 'asap', 'emergency', 'immediate', 'critical'],
        'medium': ['important', 'priority', 'attention', 'please respond'],
        'low': ['fyi', 'update', 'newsletter', 'information']
    }

    def process(self, data: str, conversation_id: str) -> Dict[str, Any]:
        """Process email content and extract relevant information"""
        try:
            # Parse email
            if isinstance(data, str):
                msg = email.message_from_string(data)
            else:
                msg = email.message_from_bytes(data)

            # Extract basic metadata
            metadata = self._extract_metadata(msg)
            
            # Extract and validate sender
            sender_info = self._validate_sender(metadata.get('from', ''))
            
            # Determine urgency
            content = self._get_email_content(msg)
            urgency = self._determine_urgency(content, msg['subject'] or '')

            # Format for CRM
            crm_format = self._format_for_crm(metadata, sender_info, content, urgency)

            result = {
                'metadata': metadata,
                'sender': sender_info,
                'urgency': urgency,
                'crm_format': crm_format,
                'status': 'success'
            }

            # Log the processing
            self.log_action(
                conversation_id=conversation_id,
                action='process_email',
                details={
                    'sender': sender_info['email'],
                    'urgency': urgency,
                    'subject': metadata.get('subject', '')
                }
            )

            # Update context
            self.update_context(conversation_id, {
                'email_sender': sender_info['email'],
                'email_urgency': urgency,
                'email_subject': metadata.get('subject', '')
            })

            return result

        except Exception as e:
            error_result = {
                'status': 'error',
                'error': f'Error processing email: {str(e)}'
            }
            self.log_action(
                conversation_id=conversation_id,
                action='process_email_error',
                details=error_result
            )
            return error_result

    def _extract_metadata(self, msg: EmailMessage) -> Dict[str, str]:
        """Extract basic email metadata"""
        return {
            'from': msg.get('from', ''),
            'to': msg.get('to', ''),
            'subject': msg.get('subject', ''),
            'date': msg.get('date', ''),
            'message_id': msg.get('message-id', ''),
            'content_type': msg.get_content_type()
        }

    def _validate_sender(self, sender: str) -> Dict[str, str]:
        """Validate and extract sender information"""
        try:
            # Extract name if present (Format: "Name <email@domain.com>")
            name_match = re.match(r'"?([^"<]+)"?\s*<?([^>]+)>?', sender)
            if name_match:
                name, email_addr = name_match.groups()
            else:
                name, email_addr = '', sender

            # Validate email
            valid = validate_email(email_addr)
            
            return {
                'name': name.strip(),
                'email': valid.email,
                'domain': valid.domain,
                'valid': True
            }
        except EmailNotValidError:
            return {
                'name': '',
                'email': sender,
                'domain': '',
                'valid': False
            }

    def _get_email_content(self, msg: EmailMessage) -> str:
        """Extract email content, handling multipart messages"""
        if msg.is_multipart():
            parts = []
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    parts.append(part.get_payload(decode=True).decode())
            return "\n".join(parts)
        else:
            return msg.get_payload(decode=True).decode()

    def _determine_urgency(self, content: str, subject: str) -> str:
        """Determine email urgency based on content and subject"""
        text = (content + " " + subject).lower()
        
        # Check for explicit urgency markers
        if any(marker in text for marker in self.URGENCY_KEYWORDS['high']):
            return 'high'
        elif any(marker in text for marker in self.URGENCY_KEYWORDS['medium']):
            return 'medium'
        elif any(marker in text for marker in self.URGENCY_KEYWORDS['low']):
            return 'low'
        
        return 'normal'

    def _format_for_crm(self, metadata: Dict[str, str], sender: Dict[str, str],
                       content: str, urgency: str) -> Dict[str, Any]:
        """Format email data for CRM system"""
        return {
            'contact': {
                'name': sender['name'],
                'email': sender['email'],
                'domain': sender['domain']
            },
            'communication': {
                'type': 'email',
                'direction': 'inbound',
                'subject': metadata.get('subject', ''),
                'body': content,
                'date': metadata.get('date', ''),
                'urgency': urgency
            },
            'metadata': {
                'message_id': metadata.get('message_id', ''),
                'thread_id': metadata.get('thread-id', ''),
                'recipients': metadata.get('to', '').split(','),
                'content_type': metadata.get('content_type', '')
            }
        } 