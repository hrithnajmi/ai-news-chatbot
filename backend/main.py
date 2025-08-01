#---------------DESCRIPTION🛠️-----------------------------
# FastAPI backend for AI News Chatbot
# Integrates Azure OpenAI with News API
# Run with: python main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
from openai import AzureOpenAI
from newsapi import NewsApiClient

# Load environment variables
load_dotenv()

# Create FastAPI instance
app = FastAPI(
    title="AI News Chatbot API",
    description="Backend API for AI News Chatbot application with Azure OpenAI integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI and News clients
env_endpoint = os.getenv("ENDPOINT")
env_api_key = os.getenv("SUBSCRIPTION_KEY")
env_api_version = os.getenv("API_VERSION")
env_base_model = os.getenv("MODEL_NAME")
env_news_api_key = os.getenv("NEWS_API_KEY")

news_client = NewsApiClient(api_key=env_news_api_key)
openai_client = AzureOpenAI(
    azure_endpoint=env_endpoint,
    api_key=env_api_key,
    api_version=env_api_version,
)

# Request models
class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []

class SummaryRequest(BaseModel):
    article: dict

# Copy your get_top_news function from aibot.py
def get_top_news(location, category=None, query=None):
    """Get the top news headlines for a given location, optionally filtered by category or query"""
    try:
        # Determine the search parameters
        if query:
            # Search by query/keyword
            top_headlines = news_client.get_everything(
                q=query,
                language='en',
                sort_by='publishedAt',
                page_size=10,
            )
        elif category:
            # Search by category
            top_headlines = news_client.get_top_headlines(
                country=location,
                category=category,  # sports, technology, business, etc.
                page_size=10,
            )
        else:
            # General news
            top_headlines = news_client.get_top_headlines(
                country=location,
                page_size=10,
            )

        articles = top_headlines.get("articles", [])
        
        if not articles:
            return [{
                "id": "no-news",
                "location": location,
                "title": "No news found.",
                "description": f"No articles available for this {'category' if category else 'query' if query else 'location'}.",
                "url": "#",
                "source": "System",
                "publishedAt": "2024-01-01",
            }]

        top_news = []
        for i, article in enumerate(articles[:5]):  # Return top 5
            top_news.append({
                "id": str(i + 1),
                "location": location,
                "title": article.get('title') or "No title",
                "description": article.get('description') or "No description available",
                "url": article.get('url') or "#",
                "source": article.get('source', {}).get('name', 'Unknown'),
                "publishedAt": article.get('publishedAt') or "2024-01-01",
            })

        return top_news
    except Exception as e:
        print(f"Error fetching news: {e}")
        return [{
            "id": "error",
            "location": location,
            "title": "Error fetching news",
            "description": f"Unable to fetch news: {str(e)}",
            "url": "#",
            "source": "System",
            "publishedAt": "2024-01-01",
        }]

# Copy your tools definition from aibot.py
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_top_news",
            "description": "Get the top news headlines based on location, category, or search query",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location name (2-letter country code), e.g. us, my, gb"
                    },
                    "category": {
                        "type": "string",
                        "description": "News category: business, entertainment, general, health, science, sports, technology",
                        "enum": ["business", "entertainment", "general", "health", "science", "sports", "technology"]
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for specific topics (use instead of category for more specific searches)"
                    }
                },
                "required": ["location"],
            }
        }
    }
]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI News Chatbot API is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-news-chatbot-backend"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint for AI responses with news integration"""
    try:
        # Build messages from conversation history
        messages = [
            {"role": "system", "content": """You are a helpful AI news assistant. When users ask for news:
    
    1. For specific topics (sports, technology, business, etc.), use the 'category' parameter
    2. For very specific queries (like "climate change", "AI developments"), use the 'query' parameter  
    3. For general news, use location only
    
    Categories available: business, entertainment, general, health, science, sports, technology
    
    Always provide brief, clean responses without listing article details since they'll be displayed separately."""},
        ]
        
        # Add conversation history (last 10 messages)
        for msg in request.conversation_history[-10:]:
            if msg.get("content"):
                messages.append({
                    "role": "user" if msg.get("type") == "user" else "assistant",
                    "content": msg.get("content", "")
                })
        
        # Add current message
        messages.append({"role": "user", "content": request.message})

        # First AI call with tools
        response = openai_client.chat.completions.create(
            model=env_base_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message

        # Handle tool calls (news fetching)
        if response_message.tool_calls:
            # Add assistant message with tool calls to conversation
            messages.append({
                "role": response_message.role,
                "content": response_message.content,
                "tool_calls": [tc.model_dump() for tc in response_message.tool_calls]
            })

            articles = []
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "get_top_news":
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Get news articles with category/query support
                    news_response = get_top_news(
                        location=function_args.get("location", "us"),
                        category=function_args.get("category"),
                        query=function_args.get("query")
                    )
                    articles = news_response
                    
                    # Add tool response to conversation
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": "get_top_news",
                        "content": json.dumps(news_response),
                    })

            # Second AI call to get final response
            final_response = openai_client.chat.completions.create(
                model=env_base_model,
                messages=messages,
            )

            final_message = final_response.choices[0].message
            
            # Generate a clean version for UI
            clean_messages = [
                {"role": "system", "content": "Generate a brief, friendly response (max 40 words) acknowledging that you found articles for the user's query. Don't list article details since they'll be displayed separately. Be conversational and helpful."},
                {"role": "user", "content": f"I searched for: {request.message} and found {len(articles)} articles. Generate a brief response."}
            ]
            
            clean_response = openai_client.chat.completions.create(
                model=env_base_model,
                messages=clean_messages,
                max_tokens=60,
            )
            
            return {
                "message": clean_response.choices[0].message.content,
                "full_message": final_message.content,  # Keep full version if needed
                "articles": articles,
                "type": "news_with_articles"
            }
        else:
            # Normal response without tools
            return {
                "message": response_message.content,
                "articles": [],
                "type": "text_response"
            }

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@app.post("/api/summarize")
async def summarize_article(request: SummaryRequest):
    """Generate AI summary for a specific article"""
    try:
        article = request.article
        
        messages = [
            {
                "role": "system",
                "content": "You are an AI that provides concise, informative summaries of news articles. Focus on key points, implications, and important details. Keep summaries clear and engaging."
            },
            {
                "role": "user",
                "content": f"Please provide a comprehensive summary of this article:\n\nTitle: {article.get('title')}\nDescription: {article.get('description')}\n\nProvide a detailed summary with key points and implications:"
            }
        ]

        response = openai_client.chat.completions.create(
            model=env_base_model,
            messages=messages,
            max_tokens=300,  # Limit summary length
        )

        return {
            "summary": response.choices[0].message.content
        }

    except Exception as e:
        print(f"Summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

# Keep your existing endpoints
@app.get("/api/news")
async def get_news():
    """Get latest news - legacy endpoint"""
    return {"news": [], "message": "Use /api/chat for AI-powered news retrieval"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🚀 Starting AI News Chatbot API on http://{host}:{port}")
    print(f"📰 News API: {'✅ Connected' if env_news_api_key else '❌ Missing'}")
    print(f"🤖 Azure OpenAI: {'✅ Connected' if env_api_key else '❌ Missing'}")
    
    uvicorn.run(app, host=host, port=port, reload=debug)