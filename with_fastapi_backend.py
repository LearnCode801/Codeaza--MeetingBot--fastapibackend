from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from chatbot.engine import respond, clear_session_memory, get_session_info
import uuid
import os
from datetime import datetime
import uvicorn
import json

app = FastAPI()

# Add CORS middleware to match Flask-CORS behavior
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
sessions = {}

@app.post("/upload")
async def upload_transcript(request: Request):
    """Upload meeting transcript and initialize session"""
    try:
        # Get JSON data exactly like Flask's request.get_json()
        try:
            data = await request.json()
        except:
            data = {}
        
        transcript = data.get('transcript', '')
        session_id = data.get('session_id', '')
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not transcript:
            return JSONResponse(
                status_code=400,
                content={'error': 'Transcript is required'}
            )
        
        # Validate transcript length
        if len(transcript) < 10:
            return JSONResponse(
                status_code=400,
                content={'error': 'Transcript too short. Please provide a valid meeting transcript.'}
            )
        
        # Save to session
        sessions[session_id] = {
            'transcript': transcript,
            'chat_history': [],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        return JSONResponse(
            status_code=200,
            content={
                'message': 'Transcript uploaded successfully',
                'session_id': session_id,
                'transcript_length': len(transcript)
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'Server error: {str(e)}'}
        )

@app.post("/chat")
async def chat(request: Request):
    """Handle chat interactions with the AI"""
    try:
        # Get JSON data exactly like Flask's request.get_json()
        try:
            data = await request.json()
        except:
            data = {}
        
        message = data.get('message', '')
        session_id = data.get('session_id', '')
        
        if not message or not session_id:
            return JSONResponse(
                status_code=400,
                content={'error': 'Message and session_id are required'}
            )
        
        # Get session data
        session_data = sessions.get(session_id)
        
        if not session_data:
            return JSONResponse(
                status_code=404,
                content={'error': 'Session not found. Please upload a transcript first.'}
            )
        
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
        
        return JSONResponse(
            status_code=200,
            content={
                'response': response_message,
                'session_id': session_id
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'Chat error: {str(e)}'}
        )

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    try:
        session_data = sessions.get(session_id)
        
        if not session_data:
            return JSONResponse(
                status_code=404,
                content={'error': 'Session not found'}
            )
        
        return JSONResponse(
            status_code=200,
            content={
                'session_id': session_id,
                'transcript_length': len(session_data['transcript']),
                'message_count': len(session_data['chat_history']),
                'created_at': session_data['created_at'],
                'last_activity': session_data['last_activity']
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'Session error: {str(e)}'}
        )

@app.get("/session/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        session_data = sessions.get(session_id)
        
        if not session_data:
            return JSONResponse(
                status_code=404,
                content={'error': 'Session not found'}
            )
        
        return JSONResponse(
            status_code=200,
            content={
                'session_id': session_id,
                'chat_history': session_data['chat_history']
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'History error: {str(e)}'}
        )

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and clear its memory"""
    try:
        if session_id in sessions:
            del sessions[session_id]
            clear_session_memory(session_id)
            return JSONResponse(
                status_code=200,
                content={'message': 'Session deleted successfully'}
            )
        else:
            return JSONResponse(
                status_code=404,
                content={'error': 'Session not found'}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'Delete error: {str(e)}'}
        )

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
        
        return JSONResponse(
            status_code=200,
            content={
                'sessions': session_list,
                'total_sessions': len(session_list)
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'List error: {str(e)}'}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            'status': 'healthy',
            'active_sessions': len(sessions),
            'google_api_key_configured': bool(os.getenv('GOOGLE_API_KEY'))
        }
    )

@app.post("/clear-all")
async def clear_all_sessions():
    """Clear all sessions (for development/testing)"""
    try:
        session_count = len(sessions)
        sessions.clear()
        
        # Clear all session memories
        from chatbot.engine import session_memory
        session_memory.clear()
        
        return JSONResponse(
            status_code=200,
            content={
                'message': f'Cleared {session_count} sessions successfully'
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'Clear error: {str(e)}'}
        )

if __name__ == '__main__':
    # Check for Google API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("WARNING: GOOGLE_API_KEY environment variable not set!")
        print("Please set your Google API key: export GOOGLE_API_KEY='your_api_key_here'")
    
    app.run(debug=True)
