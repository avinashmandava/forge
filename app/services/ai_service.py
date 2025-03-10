from openai import AsyncOpenAI
from typing import Dict, Any, Optional
import os
import json
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities like company names, contact details, and deal information from text."""
        prompt = f"""Extract relevant CRM information from the following text.
        Return a JSON object with these exact fields (all optional):
        - company_name: Company mentioned
        - contact_first_name: First name of contact
        - contact_last_name: Last name of contact
        - contact_email: Email if mentioned
        - contact_phone: Phone if mentioned
        - deal_value: Monetary value mentioned (e.g., "$500k", "$1.2M")
        - deal_stage: Stage of deal (e.g., "Initial Contact", "Proposal", "Negotiation")

        For example:
        {{
            "company_name": "Acme Corp",
            "contact_first_name": "John",
            "contact_last_name": "Smith",
            "deal_value": "$500k",
            "deal_stage": "Negotiation"
        }}

        Text: {text}"""

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "system",
                "content": "You are a helpful assistant that extracts structured CRM data from text. Always respond with valid JSON matching the exact format specified."
            }, {
                "role": "user",
                "content": prompt
            }],
            response_format={ "type": "json_object" }
        )

        try:
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return {}

    async def generate_interaction_summary(self, text: str) -> str:
        """Generate a concise summary of an interaction."""
        prompt = f"""Summarize the following interaction in a professional, concise manner.
        Focus on key points, action items, and next steps.

        Interaction: {text}"""

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "system",
                "content": "You are a helpful assistant that summarizes business interactions concisely."
            }, {
                "role": "user",
                "content": prompt
            }]
        )

        return response.choices[0].message.content

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze the sentiment and extract key insights from an interaction."""
        prompt = f"""Analyze the following interaction and provide insights in a structured format.
        Return a JSON object with these exact fields:
        - OverallSentiment: (positive, negative, or neutral)
        - KeyConcernsOrObjectionsRaised: [array of concerns]
        - LevelOfInterest: (high, medium, or low)
        - SuggestedNextSteps: [array of specific action items]

        For example:
        {{
            "OverallSentiment": "positive",
            "KeyConcernsOrObjectionsRaised": ["Integration with existing systems", "Timeline concerns"],
            "LevelOfInterest": "high",
            "SuggestedNextSteps": ["Schedule technical deep dive", "Prepare integration documentation"]
        }}

        Interaction: {text}"""

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{
                "role": "system",
                "content": "You are a helpful assistant that analyzes business interactions. Always respond with valid JSON matching the exact format specified."
            }, {
                "role": "user",
                "content": prompt
            }],
            response_format={ "type": "json_object" }
        )

        try:
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return {
                "OverallSentiment": "neutral",
                "KeyConcernsOrObjectionsRaised": [],
                "LevelOfInterest": "medium",
                "SuggestedNextSteps": ["Follow up on conversation"]
            }
