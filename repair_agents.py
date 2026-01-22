"""CrewAI agents for repair bot stages"""
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RepairAgents:
    """Factory for creating repair bot agents"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3
        )
    
    def device_discovery_agent(self) -> Agent:
        """Agent for Stage 1: Device Discovery"""
        return Agent(
            role="Device Identification Specialist",
            goal="Identify the exact device model that needs repair",
            backstory="""You are an expert technician who identifies appliances accurately.
            You ask users for their device model/name and help them locate it in the database.
            You must be conversational but focused on getting the exact device information.""",
            llm=self.llm,
            verbose=False,
            allow_delegation=False
        )
    
    def symptom_discovery_agent(self) -> Agent:
        """Agent for Stage 2: Symptom Discovery (7 sequential questions)"""
        return Agent(
            role="Symptom Assessment Specialist",
            goal="Systematically gather all relevant information about the device failure",
            backstory="""You are a technical support specialist with 20 years of experience.
            You ask clear, specific questions to understand the exact nature of the device failure.
            You track the conversation to ensure you ask exactly 7 questions in sequence.
            Each response should include only the answer to the current question, then ask the next one.""",
            llm=self.llm,
            verbose=False,
            allow_delegation=False
        )
    
    def repair_guide_agent(self) -> Agent:
        """Agent for Stage 3: Repair Guide Generation"""
        return Agent(
            role="Repair Guide Specialist",
            goal="Generate detailed step-by-step repair instructions based on device and symptoms",
            backstory="""You are a master technician with expertise in appliance repair.
            You read repair manuals from the knowledge base and create clear, safe repair instructions.
            Each step is numbered, specific, and includes safety warnings where needed.
            You provide exactly one repair step per interaction and wait for confirmation before proceeding.""",
            llm=self.llm,
            verbose=False,
            allow_delegation=False
        )
    
    def escalation_agent(self) -> Agent:
        """Agent for handling escalation to professional service"""
        return Agent(
            role="Service Escalation Specialist",
            goal="Provide clear escalation path when repair cannot be completed",
            backstory="""You are a customer service specialist trained in professional escalation.
            When repairs cannot be completed after 5 attempts, you provide clear next steps
            and professional service contact information.""",
            llm=self.llm,
            verbose=False,
            allow_delegation=False
        )


class RepairTasks:
    """Factory for creating repair bot tasks"""
    
    @staticmethod
    def device_discovery_task(agent: Agent, user_input: str) -> Task:
        """Task: Identify device"""
        return Task(
            description=f"""User input: '{user_input}'
            
            Your job is to identify if this is a known device.
            Respond with:
            1. Confirm the device model if recognized
            2. If not recognized, provide a helpful response with known device options
            
            Keep response brief and focused on device identification only.""",
            agent=agent,
            expected_output="""A brief response confirming the device or asking for clarification.
            Do not proceed with other questions."""
        )
    
    @staticmethod
    def symptom_question_task(
        agent: Agent,
        question_number: int,
        device_model: str,
        previous_answers: dict
    ) -> Task:
        """Task: Ask symptom discovery question"""
        
        questions = {
            1: "When did the issue start? (Please provide a date or timeframe, e.g., 'yesterday', 'last week')",
            2: "Describe the exact symptoms you're experiencing (e.g., no water, error codes, noises, not heating, etc.)",
            3: "Any recent changes? (e.g., power surge, moved device, installed new parts, recent service)",
            4: "Are there any error codes displayed? (If yes, list all error codes you see)",
            5: "Under what conditions does the issue happen? (e.g., cold start, after a cycle, continuously, intermittently)",
            6: "What troubleshooting have you already tried? (e.g., restarted, checked connections, etc.)",
            7: "Environment details? (e.g., installation location, water pressure if applicable, voltage stability)"
        }
        
        prev_context = "\n".join([
            f"Q{i}: {questions[i]}\nA: {previous_answers.get(i, 'N/A')}"
            for i in range(1, question_number)
        ]) if question_number > 1 else "This is the first question."
        
        return Task(
            description=f"""Device: {device_model}
            This is question {question_number} of 7 in the symptom discovery phase.
            
            Previous answers:
            {prev_context}
            
            Now ask question {question_number}: "{questions[question_number]}"
            
            Requirements:
            - Ask ONLY this question
            - Do NOT ask additional questions
            - Keep response concise and friendly""",
            agent=agent,
            expected_output=f"""The question {question_number} exactly as specified.
            Nothing more, nothing less."""
        )
    
    @staticmethod
    def repair_guide_task(
        agent: Agent,
        device_model: str,
        symptoms_summary: str,
        attempt_number: int,
        previous_steps: list
    ) -> Task:
        """Task: Generate repair guide step"""
        
        prev_steps_text = "\n".join(previous_steps) if previous_steps else "No previous steps."
        
        return Task(
            description=f"""Device: {device_model}
            Attempt: {attempt_number}/5
            Collected Symptoms: {symptoms_summary}
            
            Previous steps completed:
            {prev_steps_text}
            
            Your task:
            1. Generate the next repair step (Step {attempt_number})
            2. Make it specific, numbered, and actionable
            3. Include safety warnings if applicable
            4. Include a checkpoint question: "Did this resolve your issue? (yes/no)"
            
            Keep it brief and focused on ONE step only.""",
            agent=agent,
            expected_output=f"""Step {attempt_number}: [Specific repair instruction]
            [Safety warning if needed]
            Did this resolve your issue? (yes/no)"""
        )
    
    @staticmethod
    def escalation_task(agent: Agent, device_model: str, attempts: int) -> Task:
        """Task: Handle escalation"""
        return Task(
            description=f"""Device: {device_model}
            Repair attempts: {attempts}/5 completed without resolution
            
            Provide escalation guidance:
            1. Acknowledge the customer's efforts
            2. Explain why professional service is needed
            3. Recommend next steps
            4. Provide general guidance on contacting manufacturer support""",
            agent=agent,
            expected_output="""Professional escalation message with clear next steps"""
        )
