# app/services/nlp_service.py
import re
import json
import time
import logging
from typing import Dict, Any, Optional

import httpx
from app.config import GROQ_API_KEY, GROQ_API_URL

logger = logging.getLogger("app.nlp_service")
logger.setLevel(logging.DEBUG)

# Choose a valid Groq model:
DEFAULT_MODEL = "llama-3.1-8b-instant"


class NLPService:
    def __init__(self, model: str = DEFAULT_MODEL, timeout: int = 10):
        self.model = model
        # Make sure GROQ_API_URL is like "https://api.groq.com/openai/v1"
        self.api_url = f"{GROQ_API_URL}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        self.timeout = timeout

    async def analyze_message(self, message: str) -> Dict[str, Any]:
        """
        Returns a dict with keys:
          - intent: one of price_query, availability, rating_filter, review_request, category_query, unknown
          - entity: product name or category (or None)
          - criteria: optional dict (e.g., {"min_rating": 4.0})
        """
        # primary: ask Groq
        try:
            result = await self._call_groq_intent_api(message)
            parsed = self._safe_parse_result(result)
            if parsed and parsed.get("intent") != "unknown":
                return parsed
            # if model returned unknown, fall back to local heuristics
            logger.debug("Model returned unknown intent; falling back to local parser.")
        except Exception as e:
            logger.exception("Error calling Groq for intent extraction: %s", e)

        # fallback: deterministic local parser
        fallback = self._local_fallback_parser(message)
        logger.debug("Fallback intent result: %s", fallback)
        return fallback

    async def _call_groq_intent_api(self, message: str) -> str:
        """
        Call the Groq chat completions endpoint with a strict JSON prompt.
        Returns raw text from the model (the message content).
        Raises httpx.HTTPStatusError on non-2xx.
        """
        # strict JSON-only prompt with examples
        prompt = f"""
You are an intent and entity extraction assistant for an e-commerce chatbot.
Given the user's message below, output a single JSON object ONLY (no explanation, no extra text).
The JSON must have exactly these keys: "intent", "entity", "criteria".

- "intent" must be one of:
  "price_query", "availability", "rating_filter", "review_request", "category_query", "unknown"
- "entity" must be a product name or category string (or null)
- "criteria" must be a JSON object for additional filters (or null)
  e.g. {{ "min_rating": 4 }}

Return examples (JSON only):

Input: "What's the price of iPhone?"
Output:
{{
  "intent": "price_query",
  "entity": "iPhone",
  "criteria": null
}}

Input: "Show me electronics with ratings above 4"
Output:
{{
  "intent": "rating_filter",
  "entity": "electronics",
  "criteria": {{ "min_rating": 4 }}
}}

Input: "Do you have any laptops?"
Output:
{{
  "intent": "availability",
  "entity": "laptops",
  "criteria": null
}}

Now analyze this message and return JSON only:
Message: "{message}"
"""

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,  # deterministic
            "max_tokens": 300,
        }

        # Retry once on transient errors
        for attempt in range(2):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.api_url, headers=self.headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # Defensive extraction
                raw_text = data["choices"][0]["message"]["content"].strip()
                logger.debug("Raw Groq intent output (attempt %d): %s", attempt + 1, raw_text[:1000])
                return raw_text

        # unreachable
        raise RuntimeError("Groq API call failed after retries")

    def _safe_parse_result(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON object from raw_text and parse it.
        Returns dict or None.
        """
        # Try direct JSON first
        try:
            parsed = json.loads(raw_text)
            return self._normalize_parsed(parsed)
        except json.JSONDecodeError:
            # try to extract the first {...} JSON substring
            m = re.search(r"\{[\s\S]*\}", raw_text)
            if not m:
                logger.debug("No JSON object found in raw model output.")
                return None
            json_text = m.group(0)
            try:
                parsed = json.loads(json_text)
                return self._normalize_parsed(parsed)
            except json.JSONDecodeError:
                logger.debug("Extracted JSON substring could not be parsed.")
                return None

    def _normalize_parsed(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure the parsed structure matches our schema and normalize values.
        """
        intent = parsed.get("intent", "unknown")
        if intent not in {"price_query", "availability", "rating_filter", "review_request", "category_query", "unknown"}:
            intent = "unknown"

        entity = parsed.get("entity")
        if isinstance(entity, str):
            entity = entity.strip() or None
        else:
            entity = None

        criteria = parsed.get("criteria")
        if not isinstance(criteria, dict):
            criteria = None

        # Normalize numeric fields inside criteria (e.g., min_rating)
        if criteria and "min_rating" in criteria:
            try:
                criteria["min_rating"] = float(criteria["min_rating"])
            except Exception:
                criteria["min_rating"] = None

        return {"intent": intent, "entity": entity, "criteria": criteria}

    def _local_fallback_parser(self, message: str) -> Dict[str, Any]:
        """
        Simple deterministic parsing for common user intents using regex/keywords.
        This ensures the system has a working behavior even if the model fails.
        """
        text = message.lower().strip()

        # price queries: "price of X", "how much is X", "what's the price of X"
        m = re.search(r"(?:price of|price for|how much is|what(?:'s| is) the price of)\s+([\w\s\-]+)\??", text)
        if m:
            entity = m.group(1).strip()
            return {"intent": "price_query", "entity": entity, "criteria": None}

        # rating filter: "rating above 4", "ratings over 4.5"
        m = re.search(r"(?:rating(?:s)? (?:above|over|greater than|>=)\s*)(\d+(\.\d+)?)", text)
        if m:
            val = float(m.group(1))
            # try to find category nearby e.g., "show me electronics with rating above 4"
            cat_m = re.search(r"(?:show me|list|find)\s+([\w\s]+?)\s+(?:with|having|that have)\s+rating", text)
            cat = cat_m.group(1).strip() if cat_m else None
            return {"intent": "rating_filter", "entity": cat, "criteria": {"min_rating": val}}

        # availability: "do you have X", "any X?", "in stock"
        m = re.search(r"(?:do you have|have any|in stock|available)\s+([\w\s\-]+)\??", text)
        if m:
            entity = m.group(1).strip()
            return {"intent": "availability", "entity": entity, "criteria": None}

        # review request: "reviews for X", "tell me the reviews for X"
        m = re.search(r"(?:reviews?|opinions?) (?:for|about)\s+([\w\s\-]+)", text)
        if m:
            entity = m.group(1).strip()
            return {"intent": "review_request", "entity": entity, "criteria": None}

        # category query: "show me electronics", "list fragrances"
        m = re.search(r"(?:show me|list|find|browse)\s+([\w\s]+)", text)
        if m:
            candidate = m.group(1).strip()
            # small heuristic: if contains common category words, treat as category_query
            common_categories = {"electronics", "fragrances", "groceries", "laptops", "smartphones", "skincare", "home"}
            if any(c in candidate for c in common_categories):
                return {"intent": "category_query", "entity": candidate, "criteria": None}

        # fallback unknown
        return {"intent": "unknown", "entity": None, "criteria": None}
