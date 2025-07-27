from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Set, Any
import json
import uuid
import asyncio
from datetime import datetime
import logging

from app.models.api_models import ChatRequest, ChatResponse, ChatError
from app.services.document_service import DocumentService
from app.services.llm_service import llm_service

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

def json_serializer(obj):
    """Custom JSON serializer to handle datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Connection manager for handling multiple WebSocket connections
class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections by session ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Set to track all connection IDs for cleanup
        self.connection_ids: Set[str] = set()
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept a new WebSocket connection and return session ID"""
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.active_connections[session_id] = websocket
        self.connection_ids.add(session_id)
        logger.info(f"New WebSocket connection established: {session_id}")
        return session_id
    
    def disconnect(self, session_id: str):
        """Remove a connection from active connections"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.connection_ids:
            self.connection_ids.remove(session_id)
        logger.info(f"WebSocket connection disconnected: {session_id}")
    
    async def send_personal_message(self, message: dict, session_id: str):
        """Send a personal message to a specific connection"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message, default=json_serializer))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                # Remove dead connection
                self.disconnect(session_id)
                raise
    
    async def send_error(self, error_message: str, session_id: str, error_code: str = None):
        """Send an error message to a specific connection"""
        error_response = ChatError(
            error=error_message,
            error_code=error_code,
            session_id=session_id
        )
        await self.send_personal_message(error_response.model_dump(), session_id)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

# Global connection manager instance
manager = ConnectionManager()

# Initialize document service
document_service = DocumentService()

@router.websocket("/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with document analysis capabilities.
    
    The chat interface allows users to ask questions about their uploaded documents
    and receive AI-powered responses with relevant source citations.
    
    Message Format:
    - Incoming: {"message": "user question", "session_id": "optional", "context": {}}
    - Outgoing: {"type": "ai_response", "answer": "response", "sources": [], "financial_summary": {}}
    """
    session_id = None
    try:
        # Establish connection
        session_id = await manager.connect(websocket)
        
        # Send welcome message
        welcome_message = {
            "type": "system",
            "content": "Connected to Penny Chat. Ask me anything about your financial documents!",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(welcome_message, session_id)
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                
                # Parse the incoming message
                try:
                    message_data = json.loads(data)
                    chat_request = ChatRequest(**message_data)
                except (json.JSONDecodeError, ValueError) as e:
                    await manager.send_error(
                        f"Invalid message format: {str(e)}", 
                        session_id, 
                        "INVALID_FORMAT"
                    )
                    continue
                
                # Process the user's question
                await process_chat_message(chat_request, session_id)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {session_id}")
                break
            except json.JSONDecodeError:
                await manager.send_error(
                    "Invalid JSON format in message", 
                    session_id, 
                    "JSON_ERROR"
                )
            except Exception as e:
                logger.error(f"Error processing message for {session_id}: {e}")
                await manager.send_error(
                    f"Error processing your message: {str(e)}", 
                    session_id, 
                    "PROCESSING_ERROR"
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Clean up connection
        if session_id:
            manager.disconnect(session_id)

async def process_chat_message(chat_request: ChatRequest, session_id: str):
    """
    Process a chat message and generate an AI response using the document service.
    
    Args:
        chat_request: The parsed chat request from the user
        session_id: The WebSocket session ID
    """
    try:
        # Validate the message
        if not chat_request.message.strip():
            await manager.send_error(
                "Please provide a valid question or message", 
                session_id, 
                "EMPTY_MESSAGE"
            )
            return
        
        # Send typing indicator
        typing_message = {
            "type": "typing",
            "content": "Searching through your documents...",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(typing_message, session_id)
        
        # Query the document service for financial data
        logger.info(f"Processing query for session {session_id}: {chat_request.message}")
        
        # Prepare filters with LLM provider preference
        filters = chat_request.context if chat_request.context else {}
        if chat_request.llm_provider:
            filters['llm_provider'] = chat_request.llm_provider
        
        # Use the existing DocumentService.query_financial_data method
        query_result = await document_service.query_financial_data(
            query=chat_request.message,
            filters=filters if filters else None
        )
        
        # Check for errors in the query result
        if "error" in query_result:
            await manager.send_error(
                query_result["error"], 
                session_id, 
                "QUERY_ERROR"
            )
            return
        
        # Create the chat response
        chat_response = ChatResponse(
            answer=query_result.get("answer", "I couldn't find relevant information to answer your question."),
            sources=query_result.get("sources", []),
            financial_summary=query_result.get("financial_summary"),
            llm_provider=query_result.get("llm_provider"),
            model_used=query_result.get("model_used"),
            usage=query_result.get("usage"),
            session_id=session_id
        )
        
        # Send the response back to the client
        await manager.send_personal_message(chat_response.model_dump(), session_id)
        
        # Log successful query processing
        source_count = len(chat_response.sources)
        logger.info(f"Successfully processed query for session {session_id}, found {source_count} sources")
        
    except Exception as e:
        logger.error(f"Error processing chat message for session {session_id}: {e}")
        await manager.send_error(
            "I encountered an error while processing your question. Please try again.", 
            session_id, 
            "INTERNAL_ERROR"
        )

@router.get("/chat/status")
async def get_chat_status():
    """
    Get the current status of the chat service.
    
    Returns information about active connections and service health.
    """
    try:
        document_count = await document_service.get_document_count()
        
        return {
            "status": "healthy",
            "active_connections": manager.get_connection_count(),
            "indexed_documents": document_count,
            "service_info": {
                "document_service": "ready" if document_service.query_engine else "not_ready",
                "chroma_db": "connected" if document_service.collection else "disconnected"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting chat status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting service status: {str(e)}")

@router.get("/chat/providers")
async def get_llm_providers():
    """
    Get information about available LLM providers.
    
    Returns details about which providers are available, current default, and model information.
    """
    try:
        # Initialize LLM service if not already done
        if not llm_service._initialized:
            await llm_service.initialize()
        
        provider_info = llm_service.get_provider_info()
        
        return {
            "status": "success",
            "provider_info": provider_info,
            "available_providers": provider_info["available_providers"],
            "default_provider": provider_info["default_provider"],
            "provider_details": provider_info["provider_details"],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting LLM provider info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting provider information: {str(e)}")


@router.post("/chat/broadcast")
async def broadcast_system_message(message: str):
    """
    Broadcast a system message to all active chat connections.
    
    This endpoint is useful for administrative notifications or system updates.
    """
    try:
        system_message = {
            "type": "system",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected_sessions = []
        for session_id in manager.active_connections.keys():
            try:
                await manager.send_personal_message(system_message, session_id)
            except Exception as e:
                logger.warning(f"Failed to send broadcast to session {session_id}: {e}")
                disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            manager.disconnect(session_id)
        
        return {
            "message": "Broadcast sent successfully",
            "recipients": len(manager.active_connections),
            "failed": len(disconnected_sessions)
        }
    
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail=f"Error broadcasting message: {str(e)}")