"""Main flow manager orchestrating 3-stage repair bot"""
import json
from typing import Dict, Optional, List
from device_manager import DeviceManager
from qdrant_rag import QdrantRAG
from repair_agents import RepairAgents, RepairTasks

class RepairFlowManager:
    """
    Orchestrates the 3-stage repair flow:
    1. Device Discovery (1 interaction)
    2. Symptom Discovery (7 questions)
    3. Problem Solver (up to 5 attempts)
    """
    
    STAGES = ["device_discovery", "symptom_discovery", "problem_solver"]
    SYMPTOM_QUESTIONS = 7
    MAX_REPAIR_ATTEMPTS = 5
    
    def __init__(self):
        self.device_manager = DeviceManager()
        self.rag = QdrantRAG()
        self.agents_factory = RepairAgents()
        self.llm_available = self.agents_factory.llm is not None
        
        # Flow state
        self.current_stage_index = 0
        self.current_stage = self.STAGES[0]
        
        # Collected data
        self.device_info: Optional[Dict] = None
        self.symptoms: Dict[int, str] = {}  # {question_num: answer}
        self.repair_attempts: List[Dict] = []  # [{step: ..., result: ..., ...}]
        
        # Session metadata
        self.conversation_history: List[Dict] = []
        self.session_complete = False
        self.final_resolution = None
    
    def run_next_stage(self, user_input: str) -> Dict:
        """
        Process user input for current stage, advance if complete.
        Returns: stage response with structured data and agent response
        """
        
        if self.session_complete:
            return {
                "error": "Session already complete",
                "final_output": self.get_final_output()
            }
        
        # Route to appropriate stage handler
        if self.current_stage == "device_discovery":
            return self._handle_device_discovery(user_input)
        elif self.current_stage == "symptom_discovery":
            return self._handle_symptom_discovery(user_input)
        elif self.current_stage == "problem_solver":
            return self._handle_problem_solver(user_input)
    
    def _handle_device_discovery(self, user_input: str) -> Dict:
        """Stage 1: Validate device against known list"""
        
        # Search for device
        device_result = self.device_manager.find_device(user_input)
        
        # Store device info
        self.device_info = device_result
        
        # Create response
        response = {
            "stage": "device_discovery",
            "stage_index": 0,
            "is_complete": device_result["is_known"]
        }
        
        if device_result["is_known"]:
            # Device found - move to stage 2
            response.update({
                "structured_data": {
                    "device_model": device_result["device_model"],
                    "device_name": device_result["device_info"]["full_name"],
                    "is_known": True
                },
                "agent_response": f"""Great! I found your device: {device_result['device_info']['full_name']}
                
I'm ready to help you repair this {device_result['device_info']['device_type']}.
Let me start by asking you some questions to understand the issue better.""",
                "next_action": "Proceed to symptom discovery"
            })
            
            # Advance to stage 2
            self.current_stage_index = 1
            self.current_stage = self.STAGES[1]
        else:
            # Device not found
            known_devices = self.device_manager.get_device_list()
            devices_list = "\n".join([f"• {d}" for d in known_devices])
            
            response.update({
                "structured_data": {
                    "device_model": None,
                    "is_known": False,
                    "user_input": user_input
                },
                "agent_response": f"""I don't recognize that device model in my database.

Here are the supported devices:
{devices_list}

Could you provide your device information in one of these formats?
- Model number (e.g., SMS6EDI06E)
- Full model name (e.g., Bosch Dishwasher Serie 6 SMS6EDI06E)
- Manufacturer and type (e.g., Bosch Dishwasher)

Or contact support for guidance on unlisted devices.""",
                "next_action": "Try another device name"
            })
        
        self.conversation_history.append({
            "stage": "device_discovery",
            "user_input": user_input,
            "response": response
        })
        
        return response
    
    def _handle_symptom_discovery(self, user_input: str) -> Dict:
        """Stage 2: Ask 7 sequential symptom questions"""
        
        # Define all questions
        questions = {
            1: "When did the issue start? (e.g., 'yesterday', 'last week', 'a month ago')",
            2: "Describe the exact symptoms (e.g., no water, error codes, noises, not heating)",
            3: "Any recent changes? (e.g., power surge, moved, new parts, recent service)",
            4: "Are there any error codes displayed? (If yes, list all of them)",
            5: "Under what conditions does it happen? (e.g., cold start, after cycle, continuously)",
            6: "What troubleshooting have you already tried? (e.g., restarted, checked connections)",
            7: "Environment details? (installation location, water pressure, electrical stability)"
        }
        
        # Which question number should we store an answer for?
        # If symptoms dict is empty, user is answering question 1
        # If symptoms has 1 answer, user is answering question 2, etc.
        if user_input:
            answer_question_num = len(self.symptoms) + 1
            self.symptoms[answer_question_num] = user_input
        
        # Which question should we ask next?
        next_question_num = len(self.symptoms) + 1
        
        response = {
            "stage": "symptom_discovery",
            "stage_index": 1,
            "question_number": next_question_num,
            "total_questions": self.SYMPTOM_QUESTIONS
        }
        
        # All 7 questions have been answered - move to stage 3
        if len(self.symptoms) >= self.SYMPTOM_QUESTIONS:
            response.update({
                "is_complete": True,
                "structured_data": {
                    "symptoms": self.symptoms,
                    "symptom_summary": self._build_symptom_summary()
                },
                "agent_response": f"""Excellent! I've gathered all the information I need.

Summary of what you reported:
{self._build_symptom_summary()}

Now let me search our repair database for solutions that match your device and these symptoms.""",
                "next_action": "Move to problem solver stage"
            })
            
            # Advance to stage 3
            self.current_stage_index = 2
            self.current_stage = self.STAGES[2]
        
        else:
            # Ask next question
            next_question = questions[next_question_num]
            
            response.update({
                "is_complete": False,
                "current_question": next_question,
                "agent_response": next_question,
                "progress_text": f"Question {next_question_num} of {self.SYMPTOM_QUESTIONS}"
            })
        
        self.conversation_history.append({
            "stage": "symptom_discovery",
            "question": next_question_num,
            "user_input": user_input,
            "response": response
        })
        
        return response
    
    def _handle_problem_solver(self, user_input: str) -> Dict:
        """Stage 3: Generate repair steps, max 5 attempts"""
        
        attempt_number = len(self.repair_attempts) + 1
        
        response = {
            "stage": "problem_solver",
            "stage_index": 2,
            "attempt": attempt_number,
            "max_attempts": self.MAX_REPAIR_ATTEMPTS
        }
        
        # Process previous attempt result
        if attempt_number > 1 and self.repair_attempts:
            last_attempt = self.repair_attempts[-1]
            
            if user_input.lower() in ["yes", "y", "solved", "fixed", "resolved"]:
                # Problem solved!
                response.update({
                    "is_complete": True,
                    "resolved": True,
                    "structured_data": {
                        "device_model": self.device_info["device_model"],
                        "symptoms": self.symptoms,
                        "repair_attempts": self.repair_attempts,
                        "resolved": True,
                        "resolution_step": attempt_number - 1
                    },
                    "agent_response": """🎉 Excellent! I'm glad I could help you resolve the issue.

Here's a summary of what we did:
""" + "\n".join([f"• {step['step']}" for step in self.repair_attempts]),
                    "next_action": "Session complete"
                })
                
                self.session_complete = True
                self.final_resolution = "success"
                
                return {**response, "final_output": self.get_final_output()}
        
        # Check if max attempts reached
        if attempt_number > self.MAX_REPAIR_ATTEMPTS:
            response.update({
                "is_complete": True,
                "resolved": False,
                "escalated": True,
                "structured_data": {
                    "device_model": self.device_info["device_model"],
                    "symptoms": self.symptoms,
                    "repair_attempts": self.repair_attempts,
                    "resolved": False,
                    "escalation_reason": "Max repair attempts reached"
                },
                "agent_response": """I've worked through 5 troubleshooting steps without resolving the issue.

This suggests the device may need professional service for:
- Internal component failure (motor, pump, compressor, etc.)
- Electrical board damage
- Gas/refrigerant system issues

**Recommended Next Steps:**
1. Contact the manufacturer's service center
2. Schedule a professional technician visit
3. Check warranty coverage
4. Request service parts if available

Thank you for working through this with me. Professional service will provide the best outcome.""",
                "next_action": "Escalation complete"
            })
            
            self.session_complete = True
            self.final_resolution = "escalated"
            
            return {**response, "final_output": self.get_final_output()}
        
        # Generate next repair step
        symptom_summary = self._build_symptom_summary()
        
        # Query RAG for solutions
        rag_results = self.rag.search_solutions(
            device_model=self.device_info["device_model"],
            symptoms_summary=symptom_summary,
            top_k=3
        )
        
        # Build repair step from RAG results
        repair_step = self._generate_repair_step(
            attempt_number,
            rag_results,
            self.repair_attempts
        )
        
        # Store attempt
        self.repair_attempts.append({
            "attempt": attempt_number,
            "step": repair_step,
            "rag_sources": [r["resolution"] for r in rag_results[:1]]
        })
        
        response.update({
            "is_complete": False,
            "resolved": None,
            "repair_step": repair_step,
            "agent_response": f"""{repair_step}

**After completing this step:**
Did this resolve your issue? (yes/no)""",
            "progress_text": f"Attempt {attempt_number} of {self.MAX_REPAIR_ATTEMPTS}"
        })
        
        self.conversation_history.append({
            "stage": "problem_solver",
            "attempt": attempt_number,
            "user_input": user_input,
            "response": response
        })
        
        return response
    
    def _build_symptom_summary(self) -> str:
        """Build readable symptom summary from Q&A"""
        questions = {
            1: "Start date",
            2: "Symptoms",
            3: "Recent changes",
            4: "Error codes",
            5: "Conditions",
            6: "Troubleshooting tried",
            7: "Environment"
        }
        
        summary_lines = []
        for q_num in range(1, self.SYMPTOM_QUESTIONS + 1):
            if q_num in self.symptoms:
                summary_lines.append(
                    f"• {questions[q_num]}: {self.symptoms[q_num]}"
                )
        
        return "\n".join(summary_lines) if summary_lines else "No symptoms recorded"
    
    def _generate_repair_step(
        self,
        attempt_number: int,
        rag_results: List[Dict],
        previous_steps: List[Dict]
    ) -> str:
        """Generate repair step from RAG results"""
        
        if rag_results:
            # Use steps from top RAG result
            top_result = rag_results[0]
            if top_result.get("steps") and attempt_number <= len(top_result["steps"]):
                return top_result["steps"][attempt_number - 1]
        
        # Fallback generic steps
        generic_steps = {
            1: "Step 1: Reset the device - turn off power for 30 seconds, then turn back on and run a test cycle",
            2: "Step 2: Check all visible connections - ensure power cord is firm, water/gas lines are connected",
            3: "Step 3: Clean filters and strainers - remove any debris that could block normal operation",
            4: "Step 4: Verify water/power supply - check that water inlet and electrical supply are working properly",
            5: "Step 5: Test individual components - if you're comfortable, use a multimeter to check electrical components"
        }
        
        return generic_steps.get(attempt_number, f"Step {attempt_number}: Unable to generate further steps - escalation recommended")
    
    def get_final_output(self) -> Dict:
        """Generate final JSON output with all collected data"""
        return {
            "session_complete": self.session_complete,
            "resolution": self.final_resolution,
            "device": {
                "model": self.device_info.get("device_model") if self.device_info else None,
                "name": self.device_info.get("device_info", {}).get("full_name") if self.device_info else None,
                "is_known": self.device_info.get("is_known") if self.device_info else False
            },
            "symptoms": self.symptoms,
            "repair_log": self.repair_attempts,
            "conversation_turns": len(self.conversation_history),
            "final_status": {
                "resolved": self.final_resolution == "success",
                "escalated": self.final_resolution == "escalated",
                "attempts_made": len(self.repair_attempts)
            }
        }
    
    def is_complete(self) -> bool:
        """Check if repair session is complete"""
        return self.session_complete
    
    def get_state_json(self) -> str:
        """Export complete state as JSON for persistence"""
        return json.dumps({
            "stage": self.current_stage,
            "device_info": self.device_info,
            "symptoms": self.symptoms,
            "repair_attempts": self.repair_attempts,
            "final_output": self.get_final_output()
        }, indent=2)
