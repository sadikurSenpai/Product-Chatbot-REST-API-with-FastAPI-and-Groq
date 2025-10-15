🤖 Product Chatbot REST API with FastAPI and Groq
This project implements a fully functional, RAG-style (Retrieval-Augmented Generation) Chatbot REST API using FastAPI. It is designed to interact with customers, intelligently answering queries about product details by leveraging data from the DummyJSON Products API and generating human-like responses using the Groq LLM API.

✨ Features
RESTful Design: Clean, modular API structure with dedicated routers and service layers.

FastAPI: High-performance, modern Python web framework providing automatic documentation (Swagger UI).

Groq Integration: Utilizes Groq's low-latency LLM API for rapid intent extraction and contextual, human-like response generation (using llama-3.1-8b-instant).

RAG Logic: The chatbot follows a specific workflow:

Intent Extraction: The LLM identifies the user's goal (e.g., price query, rating filter) and relevant entities (product name).

Data Retrieval: Relevant product facts are retrieved from the DummyJSON API based on the intent.

Response Generation: The retrieved facts are combined with the original message and fed back to the LLM to synthesize a grounded, natural-language response.

Scalable Architecture: Employs a service-based architecture for clear separation of concerns (Product Service, NLP Service, Response Service).

🚀 Getting Started
These instructions will guide you through setting up and running the project locally.

Prerequisites
Python 3.10+

A Groq API Key (available from the Groq Console)

httpx (for async HTTP requests)

uvicorn (ASGI Server)

1. Clone the Repository
git clone <repository_url>
cd fastapi_chatbot

2. Setup Virtual Environment and Install Dependencies
# Create and activate environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

3. Configure Environment Variables
Create a file named .env in the project root directory and add your configuration, replacing the placeholder key with your actual Groq API Key.

# .env
DUMMYJSON_BASE_URL=[https://dummyjson.com](https://dummyjson.com)
# 🔑 Replace with your actual Groq API Key
GROQ_API_KEY=gsk_YOUR_ACTUAL_GROQ_API_KEY
GROQ_API_URL="[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)"

4. Run the Application
Start the FastAPI server using Uvicorn:

uvicorn app.main:app --reload

The application will now be running at http://127.0.0.1:8000.

🔎 API Endpoints
You can test these endpoints interactively using the Swagger UI at: http://127.0.0.1:8000/docs.

Method

Endpoint

Description

GET

/api/products/

Fetches and returns all available products from the DummyJSON API.

POST

/api/chat/

Main chatbot endpoint. Takes a customer message and returns a human-like response.

Chat Endpoint Usage Example
Request Body (POST /api/chat)

{
  "message": "What is the price and rating of the iPhone 9?"
}

Example Successful Response

{
  "response": "The iPhone 9 is priced at $549, and it has an excellent customer rating of 4.69. It's currently in stock with a 1-year warranty. You can place your order now!"
}

📂 Project Structure
fastapi_chatbot/
│
├── app/
│   ├── main.py                 # FastAPI app instantiation, routing
│   ├── config.py               # API keys, environment variables
│   ├── models/
│   │    ├── product.py         # Pydantic model for product data
│   │    └── chat.py            # Pydantic models for chat requests/responses
│   │
│   ├── services/
│   │    ├── product_service.py # Data retrieval from DummyJSON
│   │    ├── nlp_service.py     # Groq intent understanding and entity extraction
│   │    └── response_service.py# Generates final LLM-powered response
│   │
│   ├── routers/
│   │    ├── products.py        # Router for /api/products
│   │    └── chat.py            # Router for /api/chat
│   │
├── requirements.txt
├── .env                        # Configuration file
└── README.md                   # Project documentation
