"use client";

import Image from "next/image";
import { useState } from "react";

interface Message {
  id: string;
  type: "user" | "ai";
  content: string;
  timestamp: Date;
  articles?: Article[]; // Add articles to AI messages
}

interface Article {
  id: string;
  title: string;
  description: string;
  url: string;
  source: string;
  publishedAt: string;
  aiSummary?: string; // Add this for AI-generated summaries
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [showSummaryModal, setShowSummaryModal] = useState(false);

  const determinePromptType = (input: string, hasExistingArticles: boolean) => {
    const newsKeywords = [
      "news",
      "latest",
      "breaking",
      "headlines",
      "updates",
      "happening",
      "find",
      "show me",
      "get me",
    ];
    const questionKeywords = [
      "what",
      "how",
      "why",
      "explain",
      "tell me about",
      "can you",
      "who",
      "when",
      "where",
    ];

    const lowerInput = input.toLowerCase();

    // If no articles exist, always fetch news
    if (!hasExistingArticles) {
      return "fetch_news";
    }

    // Check for explicit news requests
    if (newsKeywords.some((keyword) => lowerInput.includes(keyword))) {
      return "fetch_news";
    }

    // Check for questions about existing content
    if (questionKeywords.some((keyword) => lowerInput.includes(keyword))) {
      return "answer_question";
    }

    // Default to fetching news
    return "fetch_news";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue("");
    setIsLoading(true);

    try {
      console.log("Calling API with:", currentInput); // Debug log
      
      // Call your backend API
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: currentInput,
          conversation_history: messages.slice(-10),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("API Response:", data); // Debug log
      
      // Use AI-generated message but clean it if it contains article details
      let cleanMessage = data.message;
      
      if (data.articles && data.articles.length > 0) {
        // If the AI response is too long or contains URLs/article details, generate a clean version
        const hasUrls = /https?:\/\//.test(cleanMessage);
        const isTooLong = cleanMessage.length > 200;
        const hasArticleNumbers = /\d+\.\s/.test(cleanMessage); // Detects numbered lists
        
        if (hasUrls || isTooLong || hasArticleNumbers) {
          // Call AI again for a clean summary response
          try {
            const cleanResponse = await fetch("http://localhost:8000/api/chat", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                message: `Generate a brief, clean response (max 50 words) for someone who asked: "${currentInput}". I found ${data.articles.length} articles. Don't list article details, just acknowledge the search and mention the articles are displayed below.`,
                conversation_history: [],
              }),
            });
            
            const cleanData = await cleanResponse.json();
            cleanMessage = cleanData.message;
          } catch (cleanError) {
            console.error("Error getting clean response:", cleanError);
            // Fallback to smart template if clean AI call fails
            const topics = currentInput.toLowerCase().includes('tech') ? 'technology' : 
                          currentInput.toLowerCase().includes('sport') ? 'sports' :
                          currentInput.toLowerCase().includes('climate') ? 'climate' : 'your topic';
            
            cleanMessage = `I found ${data.articles.length} recent articles about ${topics}. You can browse through them below and click on any article for an AI summary.`;
          }
        }
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: cleanMessage,
        timestamp: new Date(),
        articles: data.articles || undefined,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Detailed error:", error);
      console.error("Error type:", typeof error);
      console.error("Error message:", error instanceof Error ? error.message : "Unknown error");
      
      // Fallback to mock data
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content:
          "Sorry, I'm having trouble connecting to the news service. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    }

    setIsLoading(false);
  };

  const handleArticleClick = async (article: Article) => {
    setSelectedArticle(article);
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          article: article,
        }),
      });

      const data = await response.json();

      // Update selected article with AI summary
      setSelectedArticle({
        ...article,
        aiSummary: data.summary,
      });
    } catch (error) {
      console.error("Error getting summary:", error);
      setSelectedArticle({
        ...article,
        aiSummary:
          "Sorry, I couldn't generate a summary for this article right now.",
      });
    }

    setShowSummaryModal(true);
    setIsLoading(false);
  };

  const closeSummaryModal = () => {
    setShowSummaryModal(false);
    setSelectedArticle(null);
  };

  return (
    <div className="min-h-screen bg-[#212121] flex flex-col">
      {/* Header */}
      <header className="bg-[#171717] border-b border-[#2f2f2f]">
        <div className="px-4 py-3">
          <h1 className="text-2xl font-bold text-[#ececec]">
            AI News Aggregator
          </h1>
        </div>
      </header>

      {/* Chat Container */}
      <div className="flex-1 max-w-4xl mx-auto w-full px-4 py-6 flex flex-col">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto mb-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-[#b4b4b4] mt-20">
              <div className="text-4xl mb-4">🤖</div>
              <h2 className="text-xl font-semibold mb-2 text-[#ececec]">
                Ready to help you with news!
              </h2>
              <p className="text-[#b4b4b4]">
                Ask me about any topic and I'll find the latest news articles and
                summarize them for you.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="space-y-3">
                <div
                  className={`flex ${
                    message.type === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-2xl px-4 py-2 rounded-lg ${
                      message.type === "user"
                        ? "bg-[#00bcd4] text-[#ececec]"
                        : "bg-[#f44336] text-[#ececec] border border-[#2f2f2f]"
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{message.content}</p>
                  </div>
                </div>

                {/* Article Bubbles - Only show for AI messages with articles */}
                {message.type === "ai" && message.articles && message.articles.length > 0 && (
                  <div className="flex justify-start">
                    <div className="max-w-4xl w-full">
                      <div className="mb-3 flex items-center gap-2">
                        <div className="w-3 h-3 bg-[#00bcd4] rounded-full"></div>
                        <span className="text-sm text-[#b4b4b4]">
                          Found {message.articles.length} articles
                        </span>
                      </div>
                      
                      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
                        {message.articles.map((article) => (
                          <div
                            key={article.id}
                            onClick={() => handleArticleClick(article)}
                            className="min-w-[300px] max-w-[300px] bg-[#2f2f2f] border border-[#404040] rounded-lg p-4 cursor-pointer hover:bg-[#3a3a3a] transition-colors flex flex-col"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <span className="text-xs text-[#00bcd4] font-medium">
                                {article.source}
                              </span>
                              <span className="text-xs text-[#8e8e8e]">
                                {new Date(article.publishedAt).toLocaleDateString()}
                              </span>
                            </div>
                            <h3 className="text-sm font-semibold text-[#ececec] mb-2 line-clamp-2">
                              {article.title}
                            </h3>
                            <p className="text-xs text-[#b4b4b4] line-clamp-3 flex-grow">
                              {article.description}
                            </p>
                            <div className="mt-3 flex justify-end">
                              <span className="text-xs text-[#00bcd4] hover:text-[#00acc1]">
                                Read Summary →
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-[#171717] border border-[#2f2f2f] max-w-3xl px-4 py-3 rounded-lg">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-[#b4b4b4] rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-[#b4b4b4] rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-[#b4b4b4] rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about any news topic... (e.g., 'technology', 'climate change', 'sports')"
            className="flex-1 px-4 py-3 bg-[#2f2f2f] border border-[#404040] text-[#ececec] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#565656] placeholder-[#8e8e8e]"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-6 py-3 bg-[#00bcd4] text-[#ececec] rounded-lg hover:bg-[#00acc1] focus:outline-none focus:ring-2 focus:ring-[#565656] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </form>
      </div>

      {/* Summary Modal */}
      {showSummaryModal && selectedArticle && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-[#2f2f2f] border border-[#404040] rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-[#404040]">
              <div className="flex items-center gap-3">
                <span className="text-sm text-[#00bcd4] font-medium">
                  {selectedArticle.source}
                </span>
                <span className="text-sm text-[#8e8e8e]">
                  {new Date(selectedArticle.publishedAt).toLocaleDateString()}
                </span>
              </div>
              <button
                onClick={closeSummaryModal}
                className="text-[#b4b4b4] hover:text-[#ececec] text-xl font-semibold"
              >
                ×
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              <h2 className="text-xl font-bold text-[#ececec] mb-4 leading-tight">
                {selectedArticle.title}
              </h2>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-[#00bcd4] mb-2">
                    AI Summary
                  </h3>
                  {selectedArticle.aiSummary ? (
                    <p className="text-[#b4b4b4] leading-relaxed">
                      {selectedArticle.aiSummary}
                    </p>
                  ) : (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-[#00bcd4] border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-[#b4b4b4]">Generating AI summary...</span>
                    </div>
                  )}
                </div>

                <div className="border-t border-[#404040] pt-4">
                  <h3 className="text-sm font-semibold text-[#00bcd4] mb-2">
                    Original Description
                  </h3>
                  <p className="text-[#b4b4b4] leading-relaxed">
                    {selectedArticle.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-[#404040]">
              <button
                onClick={closeSummaryModal}
                className="px-4 py-2 bg-[#404040] text-[#ececec] rounded-lg hover:bg-[#4a4a4a] transition-colors"
              >
                Close
              </button>
              <a
                href={selectedArticle.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-[#00bcd4] text-[#ececec] rounded-lg hover:bg-[#00acc1] transition-colors"
              >
                Read Full Article
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
