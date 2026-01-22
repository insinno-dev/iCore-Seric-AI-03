"""
Service Repair Bot - Extended Usage Examples
=============================================

Detailed examples showing how to use the bot programmatically,
integrate it, and customize it.
"""

# ============================================================================
# EXAMPLE 1: Basic Usage (Programmatic)
# ============================================================================

def example_basic_usage():
    """Run a complete repair session programmatically"""
    from flow_manager import RepairFlowManager
    import json
    
    # Initialize
    flow = RepairFlowManager()
    
    # Stage 1: Device Discovery
    print("\n=== STAGE 1: Device Discovery ===")
    response = flow.run_next_stage("Bosch Dishwasher SMS6EDI06E")
    print(f"Device identified: {response['structured_data']['device_name']}")
    
    # Stage 2: Symptom Discovery (7 questions)
    print("\n=== STAGE 2: Symptoms ===")
    answers = [
        "Yesterday morning",
        "No water entering the tub",
        "Just moved to new kitchen",
        "Error code E:15",
        "Happens immediately when cycle starts",
        "Tried unplugging and waiting",
        "Normal water pressure, stable electricity"
    ]
    
    for i, answer in enumerate(answers, 1):
        response = flow.run_next_stage(answer)
        print(f"Q{i}: Answered")
    
    print(f"Symptoms collected: {len(flow.symptoms)} answers")
    
    # Stage 3: Problem Solver
    print("\n=== STAGE 3: Repair ===")
    
    # Attempt 1
    response = flow.run_next_stage("")  # Trigger first step
    print(f"Attempt 1: {response['repair_step'][:50]}...")
    
    # User says no
    response = flow.run_next_stage("No")
    print(f"Result: Didn't work, trying step 2")
    
    # Attempt 2 - success
    response = flow.run_next_stage("Yes")
    print(f"Result: Fixed! 🎉")
    
    # Export final data
    final = flow.get_final_output()
    print("\n=== FINAL OUTPUT ===")
    print(json.dumps(final, indent=2))


# ============================================================================
# EXAMPLE 2: Error Handling & Unknown Devices
# ============================================================================

def example_unknown_device():
    """Handle device not in database"""
    from flow_manager import RepairFlowManager
    
    flow = RepairFlowManager()
    
    # Try unknown device
    response = flow.run_next_stage("Sony Television ABC123")
    
    if not response['structured_data']['is_known']:
        print("❌ Device not found")
        print(f"User input was: {response['structured_data']['user_input']}")
        
        # Provide device list
        from device_manager import DeviceManager
        dm = DeviceManager()
        devices = dm.get_device_list()
        
        print("\nSupported devices:")
        for device in devices:
            print(f"  • {device}")
        
        # Try again with known device
        print("\nRetrying with known device...")
        response = flow.run_next_stage("Bosch Dishwasher SMS6EDI06E")
        
        if response['structured_data']['is_known']:
            print("✅ Device found!")


# ============================================================================
# EXAMPLE 3: State Persistence
# ============================================================================

def example_state_persistence():
    """Save and load session state"""
    from flow_manager import RepairFlowManager
    import json
    
    # Create and run partial session
    flow = RepairFlowManager()
    flow.run_next_stage("Bosch Dishwasher SMS6EDI06E")
    
    # Save state
    state_json = flow.get_state_json()
    with open("repair_backup.json", "w") as f:
        f.write(state_json)
    print("✓ State saved to repair_backup.json")
    
    # Could load and restore state later
    with open("repair_backup.json", "r") as f:
        saved_state = json.load(f)
    print(f"✓ State restored: {saved_state['stage']}")


# ============================================================================
# EXAMPLE 4: Custom Device Database
# ============================================================================

def example_custom_devices():
    """Add custom devices to database"""
    from device_manager import DeviceManager
    
    dm = DeviceManager()
    
    # Access database
    print("Current devices:")
    for key, device in dm.DEVICE_DATABASE.items():
        print(f"  {device['full_name']}")
    
    # Add custom device (modify device_manager.py)
    # new_device = {
    #     "manufacturer": "Custom Brand",
    #     "model": "CUSTOM001",
    #     "device_type": "Custom Device",
    #     "full_name": "Custom Brand Custom Device CUSTOM001"
    # }
    # dm.DEVICE_DATABASE["custom_brand_custom001"] = new_device
    
    # Then use it
    # result = dm.find_device("Custom Brand CUSTOM001")
    # assert result["is_known"] == True


# ============================================================================
# EXAMPLE 5: RAG Integration & Custom Manuals
# ============================================================================

def example_rag_and_manuals():
    """Search RAG and add custom repair manuals"""
    from qdrant_rag import QdrantRAG
    
    rag = QdrantRAG()
    
    # Search for existing solutions
    print("\n=== Searching for repair solutions ===")
    solutions = rag.search_solutions(
        device_model="SMS6EDI06E",
        symptoms_summary="No water entry, error E:15",
        top_k=3
    )
    
    if solutions:
        print(f"Found {len(solutions)} solutions:")
        for i, sol in enumerate(solutions, 1):
            print(f"\n{i}. {sol['resolution']}")
            print(f"   Symptoms: {sol['symptoms']}")
            print(f"   Steps: {len(sol['steps'])} steps")
    
    # Add custom repair manual
    print("\n=== Adding custom repair manual ===")
    manual = {
        "device_model": "SMS6EDI06E",
        "device_name": "Bosch Dishwasher SMS6EDI06E",
        "symptoms": "Leaking water from bottom",
        "steps": [
            "Step 1: Turn off water supply",
            "Step 2: Remove lower panel",
            "Step 3: Inspect seal on water inlet",
            "Step 4: Replace seal if damaged"
        ],
        "resolution": "Water inlet seal replacement"
    }
    
    success = rag.add_manual(manual)
    if success:
        print("✓ Manual added successfully")
    else:
        print("❌ Failed to add manual")


# ============================================================================
# EXAMPLE 6: Streamlit Integration
# ============================================================================

def example_streamlit_integration():
    """How to integrate with Streamlit (excerpt from app.py)"""
    
    streamlit_code = """
import streamlit as st
from flow_manager import RepairFlowManager

# Initialize session state
if "flow_manager" not in st.session_state:
    st.session_state.flow_manager = RepairFlowManager()
    st.session_state.messages = []

flow = st.session_state.flow_manager

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Get user input
user_input = st.chat_input("Type your response...")

if user_input:
    # Add to messages
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Process with flow manager
    response = flow.run_next_stage(user_input)
    agent_message = response.get("agent_response", "")
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": agent_message
    })
    
    # Show completion
    if response.get("is_complete"):
        if response.get("resolved"):
            st.success("✓ Issue resolved!")
        elif response.get("escalated"):
            st.warning("⚠ Professional service needed")
    
    st.rerun()
    """
    print(streamlit_code)


# ============================================================================
# EXAMPLE 7: CrewAI Agent Customization
# ============================================================================

def example_custom_agents():
    """Customize agents for specific use cases"""
    
    python_code = """
from crewai import Agent
from langchain_openai import ChatOpenAI

# Create custom agent
custom_agent = Agent(
    role="Advanced Repair Technician",
    goal="Provide expert repair guidance for complex issues",
    backstory='''You are a master repair technician with 30 years of experience.
    You specialize in complex appliance repairs and can diagnose issues others cannot.
    You always prioritize safety and provide detailed warnings.''',
    llm=ChatOpenAI(model="gpt-4o-mini"),
    verbose=True,
    allow_delegation=False
)

# Use in repair flow
# task = Task(description=..., agent=custom_agent)
# crew = Crew(agents=[custom_agent], tasks=[task])
# result = crew.kickoff()
    """
    print(python_code)


# ============================================================================
# EXAMPLE 8: API Response Handling
# ============================================================================

def example_response_handling():
    """Handle different response types"""
    from flow_manager import RepairFlowManager
    
    flow = RepairFlowManager()
    response = flow.run_next_stage("Bosch Dishwasher SMS6EDI06E")
    
    # Check stage
    stage = response["stage"]
    print(f"Current stage: {stage}")
    
    # Handle device discovery
    if stage == "device_discovery":
        if response.get("is_complete"):
            device = response["structured_data"]["device_name"]
            print(f"✓ Device identified: {device}")
        else:
            print("❌ Device not found")
    
    # Handle symptom discovery
    elif stage == "symptom_discovery":
        question = response.get("current_question")
        progress = response.get("progress_text")
        print(f"{progress}: {question[:50]}...")
    
    # Handle problem solver
    elif stage == "problem_solver":
        attempt = response["attempt"]
        max_attempts = response["max_attempts"]
        print(f"Attempt {attempt}/{max_attempts}")
        
        if response.get("is_complete"):
            if response.get("resolved"):
                print("✓ Problem solved!")
            elif response.get("escalated"):
                print("⚠ Escalated to professional service")


# ============================================================================
# EXAMPLE 9: Batch Processing Sessions
# ============================================================================

def example_batch_processing():
    """Process multiple repair sessions"""
    from flow_manager import RepairFlowManager
    import json
    from datetime import datetime
    
    sessions = []
    
    test_cases = [
        {
            "device": "Bosch Dishwasher SMS6EDI06E",
            "symptoms": ["Yesterday", "No water", "None", "E:15", "Startup", "None", "Normal"]
        },
        {
            "device": "Samsung Refrigerator RF32CG5100",
            "symptoms": ["Week ago", "Not cooling", "None", "None", "Always", "Reset", "Normal"]
        }
    ]
    
    for test_case in test_cases:
        flow = RepairFlowManager()
        
        # Device discovery
        flow.run_next_stage(test_case["device"])
        
        # Symptoms
        for symptom in test_case["symptoms"]:
            flow.run_next_stage(symptom)
        
        # Simulate repair attempt
        flow.run_next_stage("")  # First step
        flow.run_next_stage("Yes")  # Resolved
        
        # Store session
        sessions.append({
            "timestamp": datetime.now().isoformat(),
            "result": flow.get_final_output()
        })
    
    # Save all sessions
    with open("batch_sessions.json", "w") as f:
        json.dump(sessions, f, indent=2)
    
    print(f"✓ Processed {len(sessions)} sessions")


# ============================================================================
# EXAMPLE 10: Integration with External Systems
# ============================================================================

def example_external_integration():
    """Integrate with ticketing systems, databases, etc."""
    
    python_code = """
from flow_manager import RepairFlowManager
import requests  # For external APIs
import json

class RepairBotIntegration:
    '''Integrate repair bot with external systems'''
    
    def __init__(self, ticket_api_url):
        self.flow = RepairFlowManager()
        self.ticket_api = ticket_api_url
    
    def create_support_ticket(self, session_data):
        '''Create support ticket from repair session'''
        payload = {
            "device": session_data["device"]["model"],
            "issue": "\\n".join(session_data["symptoms"].values()),
            "repair_steps": len(session_data["repair_log"]),
            "resolved": session_data["final_status"]["resolved"]
        }
        
        response = requests.post(f"{self.ticket_api}/tickets", json=payload)
        return response.json()
    
    def send_to_warehouse(self, device_model):
        '''Send request to parts warehouse system'''
        # Implementation for parts ordering
        pass
    
    def log_to_database(self, session_data):
        '''Log session to analytics database'''
        # Implementation for logging
        pass
    
    def run_session(self, user_inputs):
        '''Run repair session with integrations'''
        for user_input in user_inputs:
            response = self.flow.run_next_stage(user_input)
        
        final_data = self.flow.get_final_output()
        
        # Create ticket
        ticket = self.create_to_support_ticket(final_data)
        
        # Log to database
        self.log_to_database(final_data)
        
        return final_data, ticket
    """
    print(python_code)


# ============================================================================
# MAIN: Run Examples
# ============================================================================

if __name__ == "__main__":
    import sys
    
    examples = {
        "1": ("Basic Usage", example_basic_usage),
        "2": ("Unknown Device Handling", example_unknown_device),
        "3": ("State Persistence", example_state_persistence),
        "4": ("Custom Devices", example_custom_devices),
        "5": ("RAG & Manuals", example_rag_and_manuals),
        "6": ("Streamlit Integration", example_streamlit_integration),
        "7": ("Custom Agents", example_custom_agents),
        "8": ("Response Handling", example_response_handling),
        "9": ("Batch Processing", example_batch_processing),
        "10": ("External Integration", example_external_integration),
    }
    
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║        Service Repair Bot - Usage Examples                ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    print("Available examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    print("\nRun with: python examples.py <number>")
    print("Example: python examples.py 1")
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num in examples:
            name, func = examples[example_num]
            print(f"\n=== {name.upper()} ===\n")
            func()
        else:
            print(f"❌ Example {example_num} not found")
