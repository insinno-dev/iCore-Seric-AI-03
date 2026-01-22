"""Streamlit Chat UI for Service Repair Bot"""
import streamlit as st
import json
from flow_manager import RepairFlowManager
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Configure Streamlit page
st.set_page_config(
    page_title="Seric - Service Repair Bot",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stage-badge {
        display: inline-block;
        padding: 8px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        margin: 5px 5px 5px 0;
    }
    
    .stage-active {
        background-color: #4CAF50;
        color: white;
    }
    
    .stage-pending {
        background-color: #e0e0e0;
        color: #666;
    }
    
    .stage-complete {
        background-color: #2196F3;
        color: white;
    }
    
    .progress-container {
        margin: 20px 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .escalation-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .info-box {
        background-color: #e7f3ff;
        border: 1px solid #b3d9ff;
        color: #004085;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "flow_manager" not in st.session_state:
    st.session_state.flow_manager = RepairFlowManager()
    st.session_state.messages = []

# Page title and header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🔧 SERIC - Service Repair Assistant")
    st.markdown("*Guided troubleshooting for your devices*")

with col2:
    st.markdown("### Status")
    if st.session_state.flow_manager.is_complete():
        st.success("✅ Complete")
    else:
        st.info("🔄 In Progress")

# Show warnings for missing API keys
flow = st.session_state.flow_manager
if not flow.llm_available:
    st.warning("⚠️ **OpenAI API key not configured** - AI features are limited. Add OPENAI_API_KEY to .env file to enable full functionality.")

if not flow.rag.voyage_client:
    st.info("ℹ️ **VoyageAI embeddings disabled** - Using alternative search method. Optimal performance requires VOYAGE_API_KEY in .env.")

# Display progress
st.markdown("### Repair Progress")

col1, col2, col3 = st.columns(3)

with col1:
    if flow.current_stage == "device_discovery":
        st.markdown('<span class="stage-badge stage-active">1. Device Discovery</span>', unsafe_allow_html=True)
    elif flow.current_stage_index > 0:
        st.markdown('<span class="stage-badge stage-complete">1. Device Discovery ✓</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="stage-badge stage-pending">1. Device Discovery</span>', unsafe_allow_html=True)

with col2:
    if flow.current_stage == "symptom_discovery":
        question_num = len(flow.symptoms) + 1
        st.markdown(f'<span class="stage-badge stage-active">2. Symptoms ({question_num}/7)</span>', unsafe_allow_html=True)
    elif flow.current_stage_index > 1:
        st.markdown('<span class="stage-badge stage-complete">2. Symptoms (7/7) ✓</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="stage-badge stage-pending">2. Symptoms</span>', unsafe_allow_html=True)

with col3:
    if flow.current_stage == "problem_solver":
        attempt_num = len(flow.repair_attempts) + 1
        st.markdown(f'<span class="stage-badge stage-active">3. Repair ({attempt_num}/5)</span>', unsafe_allow_html=True)
    elif flow.current_stage_index > 2:
        st.markdown('<span class="stage-badge stage-complete">3. Repair ✓</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="stage-badge stage-pending">3. Repair</span>', unsafe_allow_html=True)

st.divider()

# Device info display
if flow.device_info and flow.device_info.get("is_known"):
    st.markdown(f"**📱 Device:** {flow.device_info['device_info']['full_name']}")

# Chat messages
st.markdown("### Conversation")

for i, message in enumerate(st.session_state.messages):
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.write(message["content"])
    else:
        with st.chat_message("user", avatar="👤"):
            st.write(message["content"])

# Input section
st.divider()

# Debug sidebar
with st.sidebar:
    st.markdown("### 🔍 Debug Info")
    st.write(f"**Current Stage:** {flow.current_stage}")
    st.write(f"**Stage Index:** {flow.current_stage_index}")
    if flow.current_stage == "symptom_discovery":
        st.write(f"**Symptom Questions:** {len(flow.symptoms)}/7")
    elif flow.current_stage == "problem_solver":
        st.write(f"**Repair Attempts:** {len(flow.repair_attempts)}/5")
    st.divider()
    st.write(f"**Device Known:** {flow.device_info.get('is_known') if flow.device_info else 'N/A'}")
    st.write(f"**Session Complete:** {flow.session_complete}")

if not flow.is_complete():
    user_input = st.chat_input(
        placeholder="Type your response here...",
        key="user_input"
    )
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Process with flow manager
        try:
            response = flow.run_next_stage(user_input)
            
            # Extract agent response
            if "error" in response:
                agent_msg = response.get("error", "An error occurred")
            else:
                agent_msg = response.get("agent_response", "")
            
            # Add agent message to chat
            st.session_state.messages.append({
                "role": "assistant",
                "content": agent_msg
            })
            
            # Handle completion
            if response.get("is_complete"):
                if response.get("resolved"):
                    st.markdown("""
                    <div class="success-box">
                    <strong>✅ Issue Resolved!</strong><br>
                    Your device has been successfully repaired. Thank you for using the Service Repair Assistant.
                    </div>
                    """, unsafe_allow_html=True)
                elif response.get("escalated"):
                    st.markdown("""
                    <div class="escalation-box">
                    <strong>⚠️ Professional Service Recommended</strong><br>
                    The issue requires professional service. Please contact manufacturer support.
                    </div>
                    """, unsafe_allow_html=True)
            
            st.rerun()
        
        except Exception as e:
            st.error(f"Error processing request: {str(e)}")
            st.session_state.messages.pop()

else:
    # Session complete - show final output
    st.success("✅ SERIC - Repair Session Complete!")
    
    final_output = flow.get_final_output()
    
    with st.expander("📋 Final Report", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Device Information")
            st.json({
                "Model": final_output["device"]["model"],
                "Name": final_output["device"]["name"],
                "Known": final_output["device"]["is_known"]
            })
        
        with col2:
            st.subheader("Resolution")
            st.json({
                "Status": final_output["resolution"].upper(),
                "Resolved": final_output["final_status"]["resolved"],
                "Attempts": final_output["final_status"]["attempts_made"]
            })
        
        st.subheader("Symptoms Collected")
        for q_num, answer in final_output["symptoms"].items():
            st.write(f"**Q{q_num}:** {answer}")
        
        if final_output["repair_log"]:
            st.subheader("Repair Steps Taken")
            for attempt in final_output["repair_log"]:
                st.write(f"**Attempt {attempt['attempt']}:** {attempt['step']}")
    
    # Export options
    st.divider()
    st.subheader("📥 Export Session")
    
    col1, col2 = st.columns(2)
    
    with col1:
        json_str = json.dumps(final_output, indent=2)
        st.download_button(
            label="Download as JSON",
            data=json_str,
            file_name="repair_session.json",
            mime="application/json"
        )
    
    with col2:
        # Create CSV-like export
        csv_data = "Stage,Details,Value\n"
        csv_data += f"Device,Model,{final_output['device']['model']}\n"
        csv_data += f"Device,Name,{final_output['device']['name']}\n"
        csv_data += f"Resolution,Status,{final_output['resolution']}\n"
        csv_data += f"Resolution,Resolved,{final_output['final_status']['resolved']}\n"
        
        st.download_button(
            label="Download as CSV",
            data=csv_data,
            file_name="repair_session.csv",
            mime="text/csv"
        )
    
    # Reset button
    if st.button("🔄 Start New Session", key="reset_button"):
        st.session_state.flow_manager = RepairFlowManager()
        st.session_state.messages = []
        st.rerun()

# Sidebar
with st.sidebar:
    st.markdown("### 📖 Help & Information")
    
    with st.expander("How to use this bot"):
        st.markdown("""
        1. **Stage 1 - Device Discovery:** Tell us what device you're repairing
        2. **Stage 2 - Symptoms:** Answer 7 diagnostic questions about the issue
        3. **Stage 3 - Repair:** Follow step-by-step instructions to fix the device
        
        After each repair step, let us know if the issue is resolved.
        """)
    
    with st.expander("Supported Devices"):
        from device_manager import DeviceManager
        dm = DeviceManager()
        devices = dm.get_device_list()
        for device in devices:
            st.write(f"• {device}")
    
    with st.expander("Troubleshooting Tips"):
        st.markdown("""
        - Be as specific as possible when describing symptoms
        - Include error codes if displayed
        - Note any recent changes to the device
        - Check water/power connections before proceeding
        """)
    
    st.divider()
    st.markdown("### ⚙️ Configuration")
    
    if st.checkbox("Show Advanced Debug Info"):
        st.json({
            "Stage": flow.current_stage,
            "Conversation Length": len(st.session_state.messages),
            "Device Known": flow.device_info.get("is_known") if flow.device_info else None,
            "Symptoms Count": len(flow.symptoms),
            "Repair Attempts": len(flow.repair_attempts)
        })
    
    # Environment check
    env_status = {
        "OPENAI_API_KEY": "✓" if os.getenv("OPENAI_API_KEY") else "✗",
        "VOYAGE_API_KEY": "✓" if os.getenv("VOYAGE_API_KEY") else "✗",
        "QDRANT_URL": "✓" if os.getenv("QDRANT_URL") else "✗ (using default)",
    }
    
    with st.expander("Environment Status"):
        for key, status in env_status.items():
            st.markdown(f"• {key}: {status}")

# Footer
st.divider()
st.markdown("""
---
**SERIC - Service Repair Bot** | Powered by insinno iCore.AI-Flux
""")
