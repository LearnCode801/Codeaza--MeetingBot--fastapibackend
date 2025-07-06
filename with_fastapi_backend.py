from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from chatbot.engine import respond, clear_session_memory, get_session_info
import uuid
import os
from datetime import datetime
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
sessions = {}

# Pydantic models for request/response validation
class TranscriptUpload(BaseModel):
    transcript: str
    session_id: Optional[str] = ""

class ChatMessage(BaseModel):
    message: str
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    transcript_length: int
    message_count: int
    created_at: str
    last_activity: str

class ChatHistoryResponse(BaseModel):
    session_id: str
    chat_history: List[Dict[str, Any]]

class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total_sessions: int

class HealthResponse(BaseModel):
    status: str
    active_sessions: int
    google_api_key_configured: bool

@app.post("/upload")
async def upload_transcript(data: TranscriptUpload):
    """Upload meeting transcript and initialize session"""
    try:
        transcript = data.transcript
        session_id = data.session_id
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not transcript:
            raise HTTPException(status_code=400, detail="Transcript is required")
        
        # Validate transcript length
        if len(transcript) < 10:
            raise HTTPException(status_code=400, detail="Transcript too short. Please provide a valid meeting transcript.")
        
        # Save to session
        sessions[session_id] = {
            'transcript': transcript,
            'chat_history': [],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        return {
            'message': 'Transcript uploaded successfully',
            'session_id': session_id,
            'transcript_length': len(transcript)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/chat")
async def chat(data: ChatMessage):
    """Handle chat interactions with the AI"""
    try:
        message = data.message
        session_id = data.session_id
        
        if not message or not session_id:
            raise HTTPException(status_code=400, detail="Message and session_id are required")
        
        # Get session data
        session_data = sessions.get(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found. Please upload a transcript first.")
        
        # Update last activity
        session_data['last_activity'] = datetime.now().isoformat()
        
        # Prepare session data for AI engine
        ai_session_data = {
            'transcript': session_data['transcript'],
            'chat_history': session_data['chat_history'],
            'session_id': session_id
        }
        
        # Add user message to chat history
        user_entry = {
            'sender': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        session_data['chat_history'].append(user_entry)
        
        # Get AI response
        response_message = respond(message, ai_session_data)
        
        # Add bot response to chat history
        bot_entry = {
            'sender': 'bot',
            'content': response_message,
            'timestamp': datetime.now().isoformat()
        }
        session_data['chat_history'].append(bot_entry)
        
        return {
            'response': response_message,
            'session_id': session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    try:
        session_data = sessions.get(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            'session_id': session_id,
            'transcript_length': len(session_data['transcript']),
            'message_count': len(session_data['chat_history']),
            'created_at': session_data['created_at'],
            'last_activity': session_data['last_activity']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session error: {str(e)}")

@app.get("/session/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        session_data = sessions.get(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            'session_id': session_id,
            'chat_history': session_data['chat_history']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History error: {str(e)}")

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and clear its memory"""
    try:
        if session_id in sessions:
            del sessions[session_id]
            clear_session_memory(session_id)
            return {'message': 'Session deleted successfully'}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    try:
        session_list = []
        for session_id, data in sessions.items():
            session_list.append({
                'session_id': session_id,
                'transcript_length': len(data['transcript']),
                'message_count': len(data['chat_history']),
                'created_at': data['created_at'],
                'last_activity': data['last_activity']
            })
        
        return {
            'sessions': session_list,
            'total_sessions': len(session_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'active_sessions': len(sessions),
        'google_api_key_configured': bool(os.getenv('GOOGLE_API_KEY'))
    }

@app.post("/clear-all")
async def clear_all_sessions():
    """Clear all sessions (for development/testing)"""
    try:
        session_count = len(sessions)
        sessions.clear()
        
        # Clear all session memories
        from chatbot.engine import session_memory
        session_memory.clear()
        
        return {
            'message': f'Cleared {session_count} sessions successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear error: {str(e)}")

if __name__ == '__main__':
    # Check for Google API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("WARNING: GOOGLE_API_KEY environment variable not set!")
        print("Please set your Google API key: export GOOGLE_API_KEY='your_api_key_here'")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)