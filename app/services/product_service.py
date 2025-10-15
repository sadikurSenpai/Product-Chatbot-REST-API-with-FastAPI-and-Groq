# app/services/product_service.py
import httpx
from typing import List
from app.config import DUMMYJSON_BASE_URL
from app.models.product import Product

class ProductService:
    def __init__(self):
        self.base_url = f"{DUMMYJSON_BASE_URL}/products"

    async def get_all_products(self, limit: int = 100) -> List[Product]:
        """
        Fetch products from DummyJSON with optional limit (default 100)
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}?limit={limit}")
            response.raise_for_status()
            data = response.json()
            products_data = data.get("products", [])
            print(f"[DEBUG] Total products fetched: {len(products_data)}")  # Optional debug
            return [Product(**p) for p in products_data]

    async def get_product_by_name(self, name: str, limit: int = 5) -> List[Product]:
        """
        Search product by name, description, or category (case-insensitive, partial match)
        Returns up to `limit` products to avoid large payloads
        """
        all_products = await self.get_all_products()
        name = name.lower().strip()

        matches = [
            p for p in all_products
            if name in p.title.lower()
            or name in p.description.lower()
            or name in p.category.lower()
        ]

        print(f"[DEBUG] Searching for '{name}' found: {[p.title for p in matches]}")
        return matches[:limit]  # limit results to avoid huge payloads

    async def filter_products_by_rating(self, min_rating: float, limit: int = 5) -> List[Product]:
        """
        Filter products based on minimum rating and return up to `limit` items
        """
        all_products = await self.get_all_products()
        filtered = [p for p in all_products if p.rating and p.rating >= min_rating]
        print(f"[DEBUG] Products with rating >= {min_rating}: {len(filtered)} found")
        return filtered[:limit]  # return only top N to avoid large payloads
