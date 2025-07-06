import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

from dotenv import load_dotenv
import os
load_dotenv()

# Memory store for each session
session_memory = {}

# Configure Gemini Flash 2.0
def get_llm():
    """Initialize and return Gemini Flash 2.0 model"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.3,
        google_api_key=api_key
    )

# Enhanced prompt template for meeting analysis
prompt_template = PromptTemplate(
    input_variables=["history", "input", "transcript"],
    template="""You are an expert meeting analyst AI assistant specialized in analyzing meeting transcripts and providing comprehensive insights.

MEETING TRANSCRIPT:
{transcript}

CONVERSATION HISTORY:
{history}

USER QUERY: {input}

INSTRUCTIONS:
- Analyze the meeting transcript thoroughly to answer user questions
- Provide specific, accurate information based on the transcript content
- When asked about participants, identify all speakers and their roles
- When asked about decisions, list concrete outcomes and action items
- When asked about what someone said, provide relevant quotes or paraphrases
- When asked for summary, provide structured overview of key topics, decisions, and outcomes
- Always reference specific parts of the transcript when possible
- If information isn't in the transcript, clearly state that
- Keep responses informative yet concise
- Use bullet points for lists when appropriate

RESPONSE GUIDELINES:
- For "who participated": List all speakers/participants mentioned
- For "what did [person] say": Summarize their key contributions
- For "decisions made": List concrete decisions and action items
- For "summary": Provide overview of agenda, key discussions, and outcomes
- For specific questions: Extract relevant information from transcript

Answer the user's question based on the meeting transcript provided above."""
)

def initialize_session_memory(session_id, transcript):
    """Initialize conversation memory for a new session"""
    if session_id not in session_memory:
        memory = ConversationBufferMemory(
            memory_key="history",
            return_messages=True
        )
        
        # Add transcript as initial context
        memory.chat_memory.add_user_message(
            f"I have uploaded a meeting transcript for analysis. Please help me understand its contents."
        )
        memory.chat_memory.add_ai_message(
            f"I've received and analyzed your meeting transcript ({len(transcript)} characters). "
            "I can help you with questions about participants, decisions, summaries, specific conversations, "
            "and any other details from the meeting. What would you like to know?"
        )
        
        session_memory[session_id] = memory
    
    return session_memory[session_id]

def update_memory_with_history(memory, chat_history):
    """Update memory with existing chat history"""
    # Clear existing memory to avoid duplication
    memory.clear()
    
    # Add chat history to memory
    for entry in chat_history:
        if entry['sender'] == 'user':
            memory.chat_memory.add_user_message(entry['content'])
        elif entry['sender'] == 'bot':
            memory.chat_memory.add_ai_message(entry['content'])

def extract_key_info(transcript):
    """Extract basic information from transcript for enhanced context"""
    # Simple extraction - can be enhanced with NLP
    lines = transcript.split('\n')
    participants = set()
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            # Assume format "Speaker: message"
            speaker = line.split(':')[0].strip()
            if speaker and len(speaker) < 50:  # Reasonable speaker name length
                participants.add(speaker)
    
    return {
        'participants': list(participants),
        'length': len(transcript),
        'lines': len(lines)
    }

def respond(user_message, session_data):
    """
    Main chatbot response function using Gemini Flash 2.0

    Args:
        user_message (str): The user's chat message
        session_data (dict): Session data containing:
            - transcript (str): The uploaded meeting transcript
            - chat_history (list): List of previous messages
            - session_id (str): Unique session identifier

    Returns:
        str: The chatbot's response
    """
    
    # Extract session data
    transcript = session_data.get("transcript", "")
    chat_history = session_data.get("chat_history", [])
    session_id = session_data.get("session_id", "")
    
    # Check if transcript is available
    if not transcript:
        return "Please upload a meeting transcript first so I can help you analyze it."
    
    try:
        # Initialize LLM
        llm = get_llm()
        
        # Initialize or get session memory
        memory = initialize_session_memory(session_id, transcript)
        
        # Update memory with chat history (excluding current message)
        if chat_history:
            # Remove the last user message since it's the current one
            history_without_current = chat_history[:-1] if chat_history else []
            update_memory_with_history(memory, history_without_current)
        
        # Create enhanced prompt with transcript context
        enhanced_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=prompt_template.template.replace("{transcript}", transcript)
        )
        
        # Create conversation chain
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            prompt=enhanced_prompt,
            verbose=False
        )
        
        # Generate response
        response = conversation.predict(input=user_message)
        
        # Update session memory
        session_memory[session_id] = memory
        
        return response
        
    except Exception as e:
        # Handle errors gracefully
        error_msg = f"I apologize, but I encountered an error while processing your request: {str(e)}"
        
        # Provide fallback response for common queries
        if any(keyword in user_message.lower() for keyword in ['summary', 'summarize']):
            return "I can see you're asking for a summary. Please ensure your Google API key is properly configured, and try again."
        elif any(keyword in user_message.lower() for keyword in ['participants', 'who']):
            return "I can see you're asking about participants. Please ensure your Google API key is properly configured, and try again."
        elif any(keyword in user_message.lower() for keyword in ['decision', 'decide']):
            return "I can see you're asking about decisions. Please ensure your Google API key is properly configured, and try again."
        
        return error_msg

def clear_session_memory(session_id):
    """Clear memory for a specific session"""
    if session_id in session_memory:
        del session_memory[session_id]

def get_session_info(session_id):
    """Get information about a session"""
    if session_id in session_memory:
        memory = session_memory[session_id]
        return {
            'session_exists': True,
            'message_count': len(memory.chat_memory.messages)
        }
    return {'session_exists': False}




