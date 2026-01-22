# Quick Start Guide - Service Repair Bot

## 5-Minute Setup

### 1. Prerequisites
- Python 3.10+
- API Keys (free tier available):
  - [OpenAI](https://platform.openai.com) - $5 free credit
  - [VoyageAI](https://dash.voyageai.com) - Free tier available
  - [Qdrant Cloud](https://qdrant.io/cloud) - Free tier

### 2. Clone and Install
```bash
# Navigate to project
cd c:\Software-insinno\iCore-Seric-AI-03

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy template
copy .env.example .env

# Edit .env with your API keys
# - OPENAI_API_KEY
# - VOYAGE_API_KEY
# - QDRANT_URL & QDRANT_API_KEY
```

### 4. Run Application
```bash
streamlit run app.py
```

Opens automatically at: `http://localhost:8501`

---

## How It Works

### 3-Stage Flow Example

**User**: "I have a Bosch Dishwasher SMS6EDI06E"
**Bot**: ✓ Identifies device, moves to Stage 2

**User**: [Answers 7 diagnostic questions about symptoms]
**Bot**: ✓ Collects symptom data, queries RAG, moves to Stage 3

**Bot**: "Step 1: Check the inlet valve..."
**User**: "Didn't work"
**Bot**: "Step 2: Check the inlet hose..."
**User**: "That worked!"
**Bot**: ✓ Generates final JSON report

### Output Example
```json
{
  "resolution": "success",
  "device": {
    "model": "SMS6EDI06E",
    "name": "Bosch Dishwasher Serie 6 SMS6EDI06E"
  },
  "symptoms": {
    "1": "Yesterday",
    "2": "No water entry",
    ...
  },
  "repair_log": [
    {"attempt": 1, "step": "Check inlet valve..."},
    {"attempt": 2, "step": "Check inlet hose..."}
  ]
}
```

---

## Testing

### Run Demo Suite
```bash
python demo.py
```

Includes:
- ✓ Successful repair (2 attempts)
- ✓ Unknown device handling
- ✓ Escalation flow (5 attempts)
- ✓ State persistence
- ✓ Unit tests for components

### Manual Test Flow
1. **Device Discovery**: Enter "Bosch Dishwasher SMS6EDI06E"
2. **Symptoms**: Answer 7 questions
3. **Repair**: Follow 1-2 steps until resolved
4. **Export**: Download JSON report

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt --upgrade
```

### "API Key Invalid"
- Verify .env file exists
- Check key hasn't expired/been revoked
- Test key directly in dashboard

### "Qdrant Connection Failed"
**Option 1: Local Qdrant (Docker)**
```bash
docker run -p 6333:6333 \
  -e QDRANT__HTTP__API_KEY=test-key \
  qdrant/qdrant
```
Then set in .env:
```
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=test-key
```

**Option 2: Qdrant Cloud**
```
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=<your-api-key>
```

### "VoyageAI Embedding Timeout"
- Check internet connection
- Verify API key is active
- Check rate limits (free tier: 50k tokens/min)

---

## File Structure
```
iCore-Seric-AI-03/
├── app.py                 # Streamlit UI
├── flow_manager.py        # 3-stage orchestration
├── device_manager.py      # Device validation
├── qdrant_rag.py         # Vector DB integration
├── repair_agents.py      # CrewAI agents
├── demo.py               # Test suite
├── requirements.txt      # Dependencies
├── .env.example          # Config template
├── .env                  # Your local config (git-ignored)
└── README.md             # Full documentation
```

---

## Advanced Usage

### Custom Device Database
Edit [device_manager.py](device_manager.py#L7):
```python
DEVICE_DATABASE = {
    "your_device_key": {
        "manufacturer": "Brand",
        "model": "XYZ123",
        "device_type": "Type",
        "full_name": "Brand Type XYZ123"
    }
}
```

### Add Repair Manuals to Qdrant
```python
from qdrant_rag import QdrantRAG

rag = QdrantRAG()
rag.add_manual({
    "device_model": "SMS6EDI06E",
    "device_name": "Bosch Dishwasher SMS6EDI06E",
    "symptoms": "Leaking water",
    "steps": ["Check seal", "Replace gasket"],
    "resolution": "Water seal failure"
})
```

### Custom LLM Model
Edit [repair_agents.py](repair_agents.py#L11):
```python
self.llm = ChatOpenAI(
    model="gpt-4",  # Or gpt-3.5-turbo
    api_key=os.getenv("OPENAI_API_KEY")
)
```

### Export Session State
```python
from flow_manager import RepairFlowManager

flow = RepairFlowManager()
# ... run session ...

# Export to JSON
state = flow.get_final_output()
import json
with open("session.json", "w") as f:
    json.dump(state, f, indent=2)
```

---

## API Reference

### RepairFlowManager
```python
flow = RepairFlowManager()

# Run conversation turn
response = flow.run_next_stage(user_input)

# Check if complete
if flow.is_complete():
    final_output = flow.get_final_output()

# Export state
json_state = flow.get_state_json()
```

### DeviceManager
```python
from device_manager import DeviceManager

dm = DeviceManager()

# Find device
result = dm.find_device("Bosch SMS6EDI06E")
# Returns: {"is_known": bool, "device_model": str, ...}

# Get all devices
devices = dm.get_device_list()

# Validate device
is_valid = dm.validate_device("bosch_dishwasher_sms6edi06e")
```

### QdrantRAG
```python
from qdrant_rag import QdrantRAG

rag = QdrantRAG()

# Search solutions
solutions = rag.search_solutions(
    device_model="SMS6EDI06E",
    symptoms_summary="No water entry",
    top_k=3
)

# Get embedding
embedding = rag.get_embedding("Device has water issue")
```

---

## Performance Notes

- **Cold start**: ~5 seconds (loading LLMs)
- **Device lookup**: <100ms
- **Embeddings**: ~500ms per query
- **RAG search**: ~1s (Qdrant)
- **LLM response**: ~2-3s per message

---

## Support & Resources

### Documentation
- [README.md](README.md) - Full reference
- [.env.example](.env.example) - Configuration
- [demo.py](demo.py) - Code examples

### External APIs
- [OpenAI Docs](https://platform.openai.com/docs)
- [VoyageAI Docs](https://docs.voyageai.com)
- [Qdrant Docs](https://qdrant.io/documentation)
- [CrewAI Docs](https://docs.crewai.com)

### Getting Help
1. Check .env configuration
2. Enable debug mode (sidebar)
3. Review terminal logs
4. Run `python demo.py` to test components

---

**Version**: 1.0  
**Updated**: January 2026  
**Status**: Production Ready ✓
