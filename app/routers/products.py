from fastapi import APIRouter
from typing import List
from app.models.product import Product
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/products", tags=["Products"])
service = ProductService()

@router.get("/", response_model=List[Product])
async def get_products():
    return await service.get_all_products()
