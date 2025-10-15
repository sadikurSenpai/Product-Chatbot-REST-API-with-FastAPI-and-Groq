from fastapi import FastAPI 
from app.routers import products, chat

app = FastAPI(title="Chatbot API") 

# Include routers 
app.include_router(products.router) 
app.include_router(chat.router) 

@app.get("/") 
async def root(): 
    return {"message": "FastAPI Chatbot is running"}