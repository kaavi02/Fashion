from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# --- User & Auth ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "India"
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# --- Measurements & AI Size Advisor ---
class MeasurementInput(BaseModel):
    gender: str = "unisex"
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    preferred_fit: str = "regular"

class MeasurementOut(MeasurementInput):
    id: int
    user_id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SizeRecommendationRequest(BaseModel):
    product_id: Optional[int] = None
    category_name: Optional[str] = "Tops"
    gender: Optional[str] = "unisex"
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    preferred_fit: Optional[str] = "regular"
    save_to_profile: bool = False

class SizeRecommendationResponse(BaseModel):
    recommended_size: str
    confidence_score: float
    fit_preference: str
    secondary_size: Optional[str] = None
    secondary_reason: Optional[str] = ""
    user_metrics: Dict[str, Any]
    size_standard_range: str
    commentary: str
    size_scores: Dict[str, float]

# --- Category & Brand ---
class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class BrandOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True

# --- Product Variants & Details ---
class VariantOut(BaseModel):
    id: int
    size: str
    color_name: str
    color_hex: str
    stock_quantity: int
    sku: str

    class Config:
        from_attributes = True

class ProductListItem(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    base_price: float
    discount_price: Optional[float] = None
    current_price: float
    discount_percent: int
    image_url: str
    gender: str
    rating: float
    reviews_count: int
    is_featured: bool
    category_name: str
    brand_name: str
    available_sizes: List[str]
    available_colors: List[Dict[str, str]]

class ProductDetail(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    base_price: float
    discount_price: Optional[float] = None
    current_price: float
    discount_percent: int
    image_url: str
    additional_images: List[str]
    material: Optional[str] = None
    care_instructions: Optional[str] = None
    gender: str
    rating: float
    reviews_count: int
    is_featured: bool
    category: CategoryOut
    brand: BrandOut
    variants: List[VariantOut]

# --- Cart ---
class CartItemAdd(BaseModel):
    variant_id: int
    quantity: int = 1
    session_id: Optional[str] = None

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemOut(BaseModel):
    id: int
    variant_id: int
    product_id: int
    product_name: str
    product_slug: str
    image_url: str
    size: str
    color_name: str
    color_hex: str
    price: float
    quantity: int
    item_total: float
    stock_quantity: int

class CartSummary(BaseModel):
    items: List[CartItemOut]
    subtotal: float
    shipping: float
    discount: float
    total: float
    total_count: int

# --- Orders & Checkout ---
class CheckoutRequest(BaseModel):
    shipping_name: str
    shipping_email: EmailStr
    shipping_phone: str
    shipping_address: str
    shipping_city: str
    shipping_state: str
    shipping_postal_code: str
    shipping_country: str = "India"
    payment_method: str = "Credit/Debit Card"
    session_id: Optional[str] = None

class OrderItemOut(BaseModel):
    id: int
    product_name: str
    size: str
    color_name: str
    price: float
    quantity: int
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    order_number: str
    status: str
    subtotal_amount: float
    shipping_amount: float
    discount_amount: float
    total_amount: float
    payment_method: str
    payment_status: str
    shipping_name: str
    shipping_email: str
    shipping_phone: str
    shipping_address: str
    shipping_city: str
    shipping_state: str
    shipping_postal_code: str
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None
    created_at: datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True

# --- Wishlist ---
class WishlistToggleResponse(BaseModel):
    product_id: int
    in_wishlist: bool
    message: str
