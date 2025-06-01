# Multi-Agent Document Processing System

A sophisticated multi-agent system that processes and routes different types of inputs (JSON, Email, PDF) to specialized agents while maintaining shared context and traceability.

## Features

- **LLM-based Intent Classification**: Uses a local HuggingFace Transformers model (DistilBERT) for document intent detection—no paid API required
- **Format Detection**: Automatically detects input format (JSON, Email, PDF)
- **Specialized Processing**: Routes to dedicated agents for specific processing
- **Persistent Memory**: Uses Redis for context and processing history
- **Command-line Interface**: Simple file processing via command line
- **GPU Acceleration**: If a CUDA-capable GPU is available, the LLM will use it automatically

## System Architecture

### 1. LLM Classifier Agent (`llm_classifier_agent.py`)
- Uses HuggingFace Transformers (DistilBERT) to classify document intent
- Supports intents: invoice, RFQ, complaint, regulation, unknown
- Determines routing to specialized agents

### 2. JSON Agent (`json_agent.py`)
- Schema inference
- Data validation
- Anomaly detection
- Structured data processing

### 3. Email Agent (`email_agent.py`)
- Sender validation
- Urgency detection
- Content analysis
- CRM-style formatting

### 4. Shared Memory (`shared_memory.py`)
- **Redis-backed** context storage
- Processing history tracking
- Cross-agent communication
- Operation traceability

## Installation

1. **Install Redis**
   - [Download and install Redis](https://redis.io/download) for your OS and start the Redis server.
   - On Windows, you can use [Memurai](https://www.memurai.com/) or [Redis for Windows](https://github.com/microsoftarchive/redis/releases).

2. **Clone the repository:**
```bash
git clone https://github.com/yourusername/agentic-ai-system.git
cd agentic-ai-system
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

   - This will install HuggingFace Transformers, torch, redis, and all other dependencies.

## Usage

Process a file using the command line:
```bash
python main.py <file_path>
```

Examples:
```bash
# Process a JSON invoice
python main.py samples/invoice.json

# Process an urgent email
python main.py samples/urgent_email.txt

# Process a complaint email
python main.py samples/complaint_email.txt
```

## Sample Files

The repository includes sample files for testing:

1. `samples/invoice.json`: A sample invoice in JSON format
   - Contains line items, amounts, and customer details
   - Tests JSON processing and validation

2. `samples/urgent_email.txt`: An urgent support request
   - Contains high-priority markers
   - Tests urgency detection and email processing

3. `samples/complaint_email.txt`: A customer complaint
   - Contains dissatisfaction indicators
   - Tests intent classification and email processing

## Output Examples

### JSON Processing
```
Processing file: samples/invoice.json
Detected format: json
Detected intent: invoice

Validated Data:
{
  "invoice_number": "INV-2024-001",
  "customer": {
    "name": "Acme Corporation",
    ...
  },
  ...
}
```

### Email Processing
```
Processing file: samples/urgent_email.txt
Detected format: email
Detected intent: rfq

Email Analysis:
From: John Smith <john.smith@client.com>
Subject: URGENT: System Downtime Issue
Urgency: high
```

## Dependencies

- `transformers`: HuggingFace Transformers for LLM-based classification
- `torch`: PyTorch backend for LLM
- `redis`: Redis client for Python
- `pdfminer.six`: PDF text extraction
- `email-validator`: Email validation
- `pydantic`: Data validation and settings management
- Other dependencies listed in `requirements.txt`

## Project Structure
```
├── main.py                 # Main script
├── base_agent.py           # Base agent class
├── llm_classifier_agent.py # LLM-based intent classifier
├── json_agent.py           # JSON processor
├── email_agent.py          # Email processor
├── shared_memory.py        # Redis-backed memory system
├── requirements.txt        # Dependencies
└── samples/                # Sample files
    ├── invoice.json
    ├── urgent_email.txt
    └── complaint_email.txt
```

## Data Flow

1. User provides file path via command line
2. Main script reads the file content
3. LLM Classifier Agent analyzes the content to determine:
   - Document format (JSON/Email)
   - Document intent (Invoice/RFQ/Complaint/Regulation/Unknown)
4. Based on classification:
   - JSON files → JSON Agent
   - Email files → Email Agent
5. Specialized agent processes the content
6. Results are stored in Redis-backed shared memory
7. Processing summary is displayed to console

Each step's results and metadata are tracked in Redis, maintaining a complete processing history that can be referenced by any agent in the system.

## Notes
- The LLM classifier uses a sentiment model (DistilBERT) as a demonstration. For best results, you can fine-tune or swap in a model trained for your specific intent classes.
- If you have a CUDA-capable GPU, the LLM will use it automatically for faster inference.
- All memory and logs are persistent as long as the Redis server is running. 