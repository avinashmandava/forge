"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card } from "@/components/ui/card"

interface Message {
  id: string
  content: string
  type: "user" | "ai"
  insights?: {
    entities?: {
      company_name?: string
      contact_first_name?: string
      contact_last_name?: string
      deal_value?: string
      deal_stage?: string
    }
    summary?: string
    analysis?: {
      OverallSentiment?: string
      KeyConcernsOrObjectionsRaised?: string[]
      LevelOfInterest?: string
      SuggestedNextSteps?: string[]
    }
  }
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      type: "user",
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8000/api/v1/crm/process-interaction/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: input }),
      })

      const data = await response.json()

      // Parse the AI analysis JSON string
      const analysis = JSON.parse(data.ai_analysis)

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.summary,
        type: "ai",
        insights: {
          entities: {
            company_name: analysis.company_name || "",
            contact_first_name: analysis.contact_first_name || "",
            contact_last_name: analysis.contact_last_name || "",
            deal_value: analysis.deal_value || "",
            deal_stage: analysis.deal_stage || "",
          },
          summary: data.summary,
          analysis: {
            OverallSentiment: analysis.OverallSentiment || "neutral",
            KeyConcernsOrObjectionsRaised: Array.isArray(analysis.KeyConcernsOrObjectionsRaised)
              ? analysis.KeyConcernsOrObjectionsRaised
              : analysis.KeyConcernsOrObjectionsRaised
                ? [analysis.KeyConcernsOrObjectionsRaised]
                : [],
            LevelOfInterest: analysis.LevelOfInterest || "medium",
            SuggestedNextSteps: Array.isArray(analysis.SuggestedNextSteps)
              ? analysis.SuggestedNextSteps
              : analysis.SuggestedNextSteps
                ? [analysis.SuggestedNextSteps]
                : [],
          }
        }
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error processing interaction:', error)
      // Add error message to chat
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "Sorry, there was an error processing your message. Please try again.",
        type: "ai",
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col p-4 md:p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">AI CRM Assistant</h1>

      <Card className="flex-grow flex flex-col mb-4 p-4">
        <ScrollArea className="flex-grow mb-4 h-[60vh]">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.type === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] ${
                    message.type === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  } rounded-lg p-3`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.insights && (
                    <Card className="mt-2 p-2 bg-background/50">
                      <p className="text-sm font-medium">Insights:</p>
                      {message.insights.entities && (
                        <div className="text-sm mt-1 space-y-1">
                          {(message.insights.entities.contact_first_name || message.insights.entities.contact_last_name) && (
                            <p>👤 Contact: {[
                              message.insights.entities.contact_first_name,
                              message.insights.entities.contact_last_name
                            ].filter(Boolean).join(" ")}</p>
                          )}
                          {message.insights.entities.company_name && (
                            <p>🏢 Company: {message.insights.entities.company_name}</p>
                          )}
                          {message.insights.entities.deal_value && (
                            <p>💰 Deal Value: {message.insights.entities.deal_value}</p>
                          )}
                          {message.insights.entities.deal_stage && (
                            <p>🎯 Stage: {message.insights.entities.deal_stage}</p>
                          )}
                        </div>
                      )}
                      {message.insights.analysis && (
                        <div className="text-sm mt-2 space-y-1 border-t pt-2">
                          {message.insights.analysis.OverallSentiment && (
                            <p>🎭 Sentiment: {message.insights.analysis.OverallSentiment}</p>
                          )}
                          {message.insights.analysis.LevelOfInterest && (
                            <p>🌟 Interest Level: {message.insights.analysis.LevelOfInterest}</p>
                          )}
                          {message.insights.analysis.KeyConcernsOrObjectionsRaised && (
                            <div>
                              <p>⚠️ Key Concerns:</p>
                              <ul className="list-disc list-inside pl-2">
                                {message.insights.analysis.KeyConcernsOrObjectionsRaised.map((concern, i) => (
                                  <li key={i}>{concern}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {message.insights.analysis.SuggestedNextSteps && (
                            <div>
                              <p>📋 Next Steps:</p>
                              <ul className="list-disc list-inside pl-2">
                                {message.insights.analysis.SuggestedNextSteps.map((step, i) => (
                                  <li key={i}>{step}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </Card>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-lg p-3">
                  <p>Thinking...</p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message here..."
            className="flex-grow"
            rows={3}
          />
          <Button type="submit" disabled={isLoading}>
            Send
          </Button>
        </form>
      </Card>
    </main>
  )
}
