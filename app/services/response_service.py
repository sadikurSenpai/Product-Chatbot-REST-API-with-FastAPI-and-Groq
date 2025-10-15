# app/services/response_service.py
import json
import httpx
from typing import List
from app.config import GROQ_API_KEY, GROQ_API_URL
from app.services.product_service import ProductService

class ResponseService:
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.model = model
        self.api_url = f"{GROQ_API_URL}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        self.product_service = ProductService()

    async def generate_response(self, nlp_result: dict, user_message: str) -> str:
        """
        Step 1: Use NLP output to fetch product info
        Step 2: Feed product info + user message to Groq for natural language response
        """
        intent = nlp_result.get("intent", "unknown")
        entity = nlp_result.get("entity")
        criteria = nlp_result.get("criteria", {})

        # Step 1: Fetch relevant product info based on intent
        product_info = []
        if intent in ["price_query", "availability", "review_request"] and entity:
            products = await self.product_service.get_product_by_name(entity)
            product_info = [p.model_dump() for p in products]

        elif intent == "rating_filter":
            min_rating = criteria.get("min_rating", 4.0)
            products = await self.product_service.filter_products_by_rating(min_rating)
            product_info = [p.model_dump() for p in products]

        if not product_info:
            product_info = [{"message": "No relevant product data found."}]

        # Step 2: Prepare prompt for Groq
        prompt = f"""
You are an e-commerce chatbot assistant.
Given the user's message and the product data, provide a **concise, human-readable response** in 1-2 sentences.

- Include the following information if available:
  - product name
  - price
  - rating
  - shipping or warranty info
- Do NOT include extra commentary or greetings.
- If no product data is found, politely say that you don’t have information on this product.

User message: "{user_message}"

Product data (JSON): {json.dumps(product_info)}
"""


        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

        # Extract Groq reply
        reply = result["choices"][0]["message"]["content"].strip()
        return reply
