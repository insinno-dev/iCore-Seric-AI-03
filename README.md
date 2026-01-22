# Service Repair Bot Configuration

## Environment Variables (.env file)

Create a `.env` file in the project root with:

```
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here

# VoyageAI Configuration
VOYAGE_API_KEY=pa_your-api-key-here

# Qdrant Cloud Configuration
QDRANT_URL=https://your-instance.qdrant.io
QDRANT_API_KEY=your-api-key-here

# Optional: Local Qdrant
# QDRANT_URL=http://localhost:6333
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
- **OpenAI**: Get API key from https://platform.openai.com
- **VoyageAI**: Get API key from https://dash.voyageai.com
- **Qdrant**: Sign up at https://qdrant.io/cloud or run locally

### 3. Run Application
```bash
streamlit run app.py
```

Access at: `http://localhost:8501`

## Architecture Overview

### 3-Stage Flow

**Stage 1: Device Discovery** (1 interaction)
- Validates device against known database
- Provides device information
- Advances to Stage 2 on success

**Stage 2: Symptom Discovery** (7 questions)
- Asks sequential diagnostic questions
- Collects comprehensive symptom data
- Builds symptom summary for RAG query

**Stage 3: Problem Solver** (up to 5 attempts)
- Queries Qdrant RAG with VoyageAI embeddings
- Generates step-by-step repair guides
- Tracks resolution through user feedback

### Core Components

- **flow_manager.py**: Orchestrates 3-stage flow and state management
- **device_manager.py**: Device validation and database lookup
- **qdrant_rag.py**: RAG integration with VoyageAI embeddings
- **repair_agents.py**: CrewAI agents for each stage
- **app.py**: Streamlit chat UI

## Data Flow

1. **User Input** → Flow Manager
2. **Device Validation** → Device Manager
3. **Symptom Collection** → State Storage
4. **RAG Query** → Qdrant (VoyageAI embeddings)
5. **Repair Generation** → CrewAI Agents
6. **Chat Response** → Streamlit UI
7. **Final Output** → JSON Export

## JSON Output Format

```json
{
  "session_complete": true,
  "resolution": "success|escalated",
  "device": {
    "model": "SMS6EDI06E",
    "name": "Bosch Dishwasher Serie 6 SMS6EDI06E",
    "is_known": true
  },
  "symptoms": {
    "1": "Started yesterday",
    "2": "No water entering",
    "3": "None recent",
    "4": "Error E:15",
    "5": "Happens on startup",
    "6": "Already checked inlet",
    "7": "Normal pressure"
  },
  "repair_log": [
    {
      "attempt": 1,
      "step": "Step 1: Check water inlet valve..."
    }
  ],
  "final_status": {
    "resolved": true,
    "escalated": false,
    "attempts_made": 1
  }
}
```

## Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Manual Testing Scenarios
1. **Known device** → Symptom questions → Successful repair
2. **Unknown device** → Device re-entry → Success
3. **Max attempts** → Escalation flow
4. **User confirms resolution** → JSON export

## Troubleshooting

**API Key Issues**
- Verify .env file exists and is readable
- Check `python-dotenv` is installed
- Load .env before imports

**Qdrant Connection**
- Local: Ensure Docker container running
- Cloud: Verify URL and API key from dashboard

**VoyageAI Embedding Errors**
- Check API key validity
- Verify text length < 8000 tokens
- Monitor rate limits

## Production Deployment

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

### Streamlit Cloud
```bash
streamlit run app.py --logger.level=warning
```

### Environment Variables (Production)
Set in deployment platform:
- OPENAI_API_KEY
- VOYAGE_API_KEY
- QDRANT_URL
- QDRANT_API_KEY

## API Response Examples

### Device Discovery Response
```json
{
  "stage": "device_discovery",
  "is_complete": true,
  "structured_data": {
    "device_model": "SMS6EDI06E",
    "device_name": "Bosch Dishwasher Serie 6 SMS6EDI06E",
    "is_known": true
  }
}
```

### Symptom Discovery Response
```json
{
  "stage": "symptom_discovery",
  "question_number": 2,
  "total_questions": 7,
  "is_complete": false,
  "current_question": "Describe the exact symptoms..."
}
```

### Problem Solver Response
```json
{
  "stage": "problem_solver",
  "attempt": 1,
  "max_attempts": 5,
  "repair_step": "Step 1: Check water inlet valve...",
  "resolved": false
}
```

## Support

For issues or questions:
1. Check .env configuration
2. Verify API key validity
3. Review logs in Streamlit terminal
4. Enable debug mode in sidebar
5. Check Qdrant collection status

---

**Version**: 1.0
**Last Updated**: January 2026
