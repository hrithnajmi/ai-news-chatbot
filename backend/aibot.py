#---------------DESCRIPTION🤖-----------------------------
# This is the main file where the AI News Chatbot is tested
# It integrates the Azure OpenAI and News API functionalities

#---------------PRE-REQUISITES-----------------------------
# 'cd backend' to navigate to the backend directory
# 'pip install -r requirements.txt' to install dependencies
# if newsapi not installed properly, run 'pip install newsapi-python'

#---------------GUIDELINES---------------------------------
# 'py aibot.py' to start the chatbot
# Input your queries such as "Get me the latest news in United States"
# See the output in the console

#---------------⚠️WARNING---------------------------------
# A problem detected where the News API only return results from America so far.
# Try use newsapitest.py📰 to test the News API functionality for different countries.
# Keep in mind that NewsAPI can only except max 100 requests per day as per free version.
# Therefore, try to minimize the number of requests to avoid hitting the limit.

import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI
from newsapi import NewsApiClient

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
env_endpoint = os.getenv("ENDPOINT")
env_api_key = os.getenv("SUBSCRIPTION_KEY")
env_api_version = os.getenv("API_VERSION")
env_base_model = os.getenv("MODEL_NAME")
env_news_api_key = os.getenv("NEWS_API_KEY") # IMPORTANT: Ensure this is set in your .env file

# Initialize the News API client
news_client = NewsApiClient(api_key=env_news_api_key)

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=env_endpoint,
    api_key=env_api_key,
    api_version=env_api_version,
)

# Define the function to get top news headlines
def get_top_news(location):
    """Get the top news headlines for a given location"""

    top_headlines = news_client.get_top_headlines(
        country=location,       # Must be 2-letter code, e.g., 'us', 'my'
        page_size=3,            # Get top 3 news articles
    )

    articles = top_headlines.get("articles", [])
    
    if not articles:
        return json.dumps([{
            "location": location,
            "title": "No news found.",
            "description": ""
        }])

    top_news = []
    for article in articles:
        top_news.append({
            "location": location,
            "title": article.get('title'),
            "description": article.get('description'),
        })

    return json.dumps(top_news)

# Define the function tool calling for the Azure OpenAI model
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_top_news",
            "description": "Get the top news headlines based on location provided",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location name (2-letter country code), e.g. us, my, gb"
                    }
                },
                "required": ["location"],
            }
        }
    }
]

# Provide how the assistant should behave
messages = [
    {
        "role": "system",
        "content": "Provide reply in point form.",
    },
]

# Start conversation
while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting the conversation.")
        break

    # Add user message
    messages.append({"role": "user", "content": user_input})

    # First assistant call (Function tool calling)
    response = client.chat.completions.create(
        model=env_base_model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    response_message = response.choices[0].message

    # If assistant triggered a function
    if response_message.tool_calls:
        # Append the assistant tool-calling message FIRST
        messages.append({
            "role": response_message.role,
            "content": response_message.content,
            "tool_calls": [tc.model_dump() for tc in response_message.tool_calls]
        })

        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "get_top_news":
                function_args = json.loads(tool_call.function.arguments)
                
                # Call the actual function
                news_response = get_top_news(
                    location=function_args.get("location")
                )

                # Append the tool's result
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "get_top_news",
                    "content": news_response,
                })

        # Second assistant call to complete the thought
        final_response = client.chat.completions.create(
            model=env_base_model,
            messages=messages,
        )

        final_message = final_response.choices[0].message
        print(f"\nAssistant: {final_message.content}\n")
        messages.append({
            "role": final_message.role,
            "content": final_message.content
        })

    else:
        # No tool call — normal reply
        print(f"\nAssistant: {response_message.content}\n")
        messages.append({
            "role": response_message.role,
            "content": response_message.content
        })
