#---------------DESCRIPTION🛠️-----------------------------
# Nothing to see here yet.
# Go to backend/newsapitest.py to test the News API functionality 📰
# Go to backend/aibot.py to test the AI News Chatbot 🤖

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create FastAPI instance
app = FastAPI(
    title="AI News Chatbot API",
    description="Backend API for AI News Chatbot application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],  # Next.js frontend URL from env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI News Chatbot API is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-news-chatbot-backend"}

# API routes will be added here
@app.get("/api/news")
async def get_news():
    """Get latest news"""
    return {"news": [], "message": "News endpoint - to be implemented"}

@app.post("/api/chat")
async def chat_endpoint(message: dict):
    """Chat endpoint for AI responses"""
    return {"response": "Chat functionality - to be implemented", "user_message": message}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    uvicorn.run(app, host=host, port=port, reload=debug)