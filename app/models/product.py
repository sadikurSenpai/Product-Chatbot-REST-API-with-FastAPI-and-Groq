from pydantic import BaseModel
from typing import List, Optional

class Product(BaseModel):
    id: int
    title: str
    description: str
    price: float
    discountPercentage: Optional[float] = None
    rating: Optional[float] = None
    stock: Optional[int] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    thumbnail: Optional[str] = None
    images: Optional[List[str]] = None
