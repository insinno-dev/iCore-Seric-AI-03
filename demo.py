"""Test and demonstration script for Service Repair Bot"""
import json
from flow_manager import RepairFlowManager

def demo_successful_repair():
    """Demo: Successful repair in 2 attempts"""
    print("\n" + "="*60)
    print("DEMO 1: Successful Repair (2 Attempts)")
    print("="*60)
    
    flow = RepairFlowManager()
    
    # Stage 1: Device Discovery
    print("\n[STAGE 1] Device Discovery")
    print("-" * 40)
    
    user_input = "Bosch Dishwasher Serie 6 SMS6EDI06E"
    print(f"User: {user_input}")
    
    response = flow.run_next_stage(user_input)
    print(f"Bot: {response['agent_response']}")
    print(f"Stage Complete: {response.get('is_complete')}")
    
    # Stage 2: Symptom Discovery (7 questions)
    print("\n[STAGE 2] Symptom Discovery")
    print("-" * 40)
    
    symptoms_answers = [
        "Yesterday morning",
        "No water entering the tub at all",
        "Just moved it to a new kitchen last week",
        "Error code E:15 displayed",
        "Happens immediately when cycle starts",
        "Already tried unplugging and waiting",
        "Water pressure at inlet seems normal, 110V electricity stable"
    ]
    
    for i, answer in enumerate(symptoms_answers, 1):
        print(f"\nUser: {answer}")
        response = flow.run_next_stage(answer)
        
        if response.get('is_complete'):
            print(f"Bot: {response['agent_response']}")
            break
        else:
            print(f"Bot: {response['agent_response']}")
    
    # Stage 3: Problem Solver
    print("\n[STAGE 3] Problem Solver")
    print("-" * 40)
    
    # Attempt 1
    print("\nAttempt 1:")
    response = flow.run_next_stage("")  # Trigger first step
    print(f"Bot: {response['agent_response']}")
    
    # User says no to attempt 1
    print("\nUser: No, that didn't work")
    response = flow.run_next_stage("No")
    print(f"Bot: {response['agent_response']}")
    
    # Attempt 2 - resolved
    print("\nAttempt 2:")
    print("User: Yes, it worked!")
    response = flow.run_next_stage("Yes")
    print(f"Bot: {response['agent_response']}")
    
    # Show final output
    print("\n[FINAL OUTPUT]")
    print("-" * 40)
    final = flow.get_final_output()
    print(json.dumps(final, indent=2))
    
    return flow


def demo_unknown_device():
    """Demo: Unknown device handling"""
    print("\n" + "="*60)
    print("DEMO 2: Unknown Device")
    print("="*60)
    
    flow = RepairFlowManager()
    
    print("\n[STAGE 1] Device Discovery")
    print("-" * 40)
    
    user_input = "Sony Television ABC123XYZ"
    print(f"User: {user_input}")
    
    response = flow.run_next_stage(user_input)
    print(f"Bot: {response['agent_response']}")
    print(f"Device Found: {response['structured_data']['is_known']}")
    
    # Try again with known device
    print("\n[Retry with known device]")
    user_input = "Samsung Refrigerator RF32CG5100"
    print(f"User: {user_input}")
    
    response = flow.run_next_stage(user_input)
    print(f"Bot: {response['agent_response']}")
    print(f"Device Found: {response['structured_data']['is_known']}")
    
    return flow


def demo_escalation():
    """Demo: Escalation after 5 failed attempts"""
    print("\n" + "="*60)
    print("DEMO 3: Escalation (Max Attempts Reached)")
    print("="*60)
    
    flow = RepairFlowManager()
    
    # Device Discovery
    print("\n[STAGE 1] Device Discovery")
    print("-" * 40)
    print("User: LG Microwave Oven LCRM1650")
    response = flow.run_next_stage("LG Microwave Oven LCRM1650")
    print(f"✓ Device identified: {response['structured_data']['device_name']}")
    
    # Quick symptom discovery
    print("\n[STAGE 2] Symptom Discovery (abbreviated)")
    print("-" * 40)
    
    for i, answer in enumerate(["One week ago", "Not heating", "No", "No codes", "Never", "Nothing", "Kitchen outlet"], 1):
        response = flow.run_next_stage(answer)
        if response.get('is_complete'):
            print(f"✓ Symptoms collected")
            break
    
    # Problem solver - all 5 attempts
    print("\n[STAGE 3] Problem Solver - Escalation Flow")
    print("-" * 40)
    
    for attempt in range(1, 6):
        print(f"\nAttempt {attempt}/5:")
        response = flow.run_next_stage("")
        print(f"Step: {response.get('repair_step', 'N/A')[:50]}...")
        
        # User says "no" to each attempt
        response = flow.run_next_stage("No")
        if response.get('is_complete'):
            print("\nEscalation triggered!")
            print(response['agent_response'][:200] + "...")
            break
    
    # Show final output
    print("\n[FINAL OUTPUT]")
    print("-" * 40)
    final = flow.get_final_output()
    print(f"Resolution: {final['resolution'].upper()}")
    print(f"Escalated: {final['final_status']['escalated']}")
    print(f"Attempts: {final['final_status']['attempts_made']}")
    
    return flow


def demo_state_persistence():
    """Demo: Saving and loading state"""
    print("\n" + "="*60)
    print("DEMO 4: State Persistence")
    print("="*60)
    
    flow = RepairFlowManager()
    
    # Run through device discovery
    print("\n[Running partial session]")
    response = flow.run_next_stage("Bosch Washing Machine WAX28E91")
    print(f"✓ Device identified")
    
    # Export state
    print("\n[Exporting state to JSON]")
    state_json = flow.get_state_json()
    print("Saved state:")
    print(state_json[:200] + "...")
    
    # Could be saved to file
    with open("repair_session_state.json", "w") as f:
        f.write(state_json)
    print("✓ State saved to repair_session_state.json")
    
    return flow


def test_device_manager():
    """Test device manager functionality"""
    print("\n" + "="*60)
    print("UNIT TEST: Device Manager")
    print("="*60)
    
    from device_manager import DeviceManager
    
    dm = DeviceManager()
    
    test_cases = [
        ("SMS6EDI06E", True),
        ("Bosch Dishwasher Serie 6 SMS6EDI06E", True),
        ("bosch dishwasher sms6edi06e", True),  # Case insensitive
        ("RF32CG5100", True),
        ("Samsung Refrigerator RF32CG5100", True),
        ("Sony TV XYZ123", False),
        ("Unknown Device", False)
    ]
    
    print("\nTesting device lookup:")
    for user_input, expected_known in test_cases:
        result = dm.find_device(user_input)
        actual_known = result["is_known"]
        status = "✓" if actual_known == expected_known else "✗"
        print(f"{status} '{user_input}' → Known: {actual_known}")
    
    print("\nSupported devices:")
    for device in dm.get_device_list():
        print(f"• {device}")
    
    return dm


def test_rag():
    """Test RAG functionality"""
    print("\n" + "="*60)
    print("UNIT TEST: Qdrant RAG")
    print("="*60)
    
    try:
        from qdrant_rag import QdrantRAG
        
        rag = QdrantRAG()
        
        print("\nSearching for repair solutions:")
        
        # Test search
        results = rag.search_solutions(
            device_model="SMS6EDI06E",
            symptoms_summary="No water entering, error E:15",
            top_k=2
        )
        
        if results:
            print(f"✓ Found {len(results)} solutions")
            for i, result in enumerate(results, 1):
                print(f"\n  Solution {i}:")
                print(f"    Device: {result['device_name']}")
                print(f"    Symptoms: {result['symptoms']}")
                print(f"    Resolution: {result['resolution']}")
        else:
            print("⚠ No results found - RAG may not be initialized")
        
        return rag
    
    except Exception as e:
        print(f"⚠ RAG test failed (expected if services not configured): {e}")
        return None


def main():
    """Run all demos and tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  SERVICE REPAIR BOT - COMPREHENSIVE DEMO & TEST SUITE  ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        # Unit tests
        print("\n\n[UNIT TESTS]")
        test_device_manager()
        test_rag()
        
        # Functional demos
        print("\n\n[FUNCTIONAL DEMOS]")
        demo_successful_repair()
        demo_unknown_device()
        demo_escalation()
        demo_state_persistence()
        
        print("\n\n" + "="*60)
        print("✓ ALL DEMOS AND TESTS COMPLETE")
        print("="*60)
        print("\nNext steps:")
        print("1. Configure .env file with your API keys")
        print("2. Run: streamlit run app.py")
        print("3. Access at: http://localhost:8501")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
