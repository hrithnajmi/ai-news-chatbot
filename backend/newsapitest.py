#---------------DESCRIPTION📰-----------------------------
# This file is to test the News API functionality

#---------------PRE-REQUISITES-----------------------------
# 'cd backend' to navigate to the backend directory
# 'pip install -r requirements.txt' to install dependencies
# if newsapi not installed properly, run 'pip install newsapi-python'

#---------------GUIDELINES---------------------------------
# 'py newsapitest.py' to see the results
# you can change the country code in the code marked ✅ below
# you can change the number of top news articles to retrieve in the code marked ✅ below

import os
import json
from dotenv import load_dotenv
from newsapi import NewsApiClient

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
env_news_api_key = os.getenv("NEWS_API_KEY")

# Initialize the News API client
news_client = NewsApiClient(api_key=env_news_api_key)

# Adjust the number of top news articles to retrieve
no_of_requests = 3 # ✅ Change this to your desired number of articles

# Define the function to get top news headlines
top_headlines = news_client.get_top_headlines(
        country= 'my', # ✅ Change this to your desired country code, e.g., 'us', 'my'
        page_size= no_of_requests
)

# Save the response to a JSON file to check the output (response.json)
with open("response.json", "w", encoding="utf-8") as f:
    json.dump(top_headlines, f, ensure_ascii=False, indent=2)

# Initialize the News API client
if top_headlines and top_headlines.get("articles"):
    print("\nTop 3 News Headlines:")
    for i, article in enumerate(top_headlines['articles']):
        print(f"{i+1}) {article['title']}: {article['description']}\n")
else:
    print("\nNo news found for the specified country.\n")