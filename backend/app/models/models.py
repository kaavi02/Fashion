from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(191), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(50), default="India")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    measurements = relationship("UserMeasurement", back_populates="user", uselist=False, cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    wishlist_items = relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan")

class UserMeasurement(Base):
    __tablename__ = "user_measurements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    gender = Column(String(20), default="unisex")  # men, women, unisex
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    preferred_fit = Column(String(30), default="regular")  # tight, regular, loose
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="measurements")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    products = relationship("Product", back_populates="category")

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)

    products = relationship("Product", back_populates="brand")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True, nullable=False)
    slug = Column(String(220), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    gender = Column(String(20), default="Unisex")  # Men, Women, Unisex
    base_price = Column(Float, nullable=False)
    discount_price = Column(Float, nullable=True)
    image_url = Column(String(500), nullable=False)
    additional_images_json = Column(Text, nullable=True)
    material = Column(String(100), nullable=True)
    care_instructions = Column(String(255), nullable=True)
    is_featured = Column(Boolean, default=False)
    rating = Column(Float, default=4.6)
    reviews_count = Column(Integer, default=18)
    created_at = Column(DateTime, default=utcnow)

    # Relationships with eager loading for sub-second page performance
    category = relationship("Category", back_populates="products", lazy="joined")
    brand = relationship("Brand", back_populates="products", lazy="joined")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan", lazy="selectin")
    wishlist_items = relationship("WishlistItem", back_populates="product", cascade="all, delete-orphan")

    @property
    def current_price(self):
        return self.discount_price if self.discount_price and self.discount_price > 0 else self.base_price

    @property
    def discount_percent(self):
        if self.discount_price and self.discount_price < self.base_price:
            return round(((self.base_price - self.discount_price) / self.base_price) * 100)
        return 0

    @property
    def additional_images(self):
        if self.additional_images_json:
            try:
                return json.loads(self.additional_images_json)
            except Exception:
                return []
        return []

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    size = Column(String(10), nullable=False)  # XS, S, M, L, XL, XXL, etc.
    color_name = Column(String(50), nullable=False)  # Black, Ivory, Navy, Olive
    color_hex = Column(String(10), nullable=False)  # #000000, #FFFFFF
    stock_quantity = Column(Integer, default=20)
    sku = Column(String(100), unique=True, nullable=False)

    product = relationship("Product", back_populates="variants")
    cart_items = relationship("CartItem", back_populates="variant", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String(100), index=True, nullable=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="cart_items")
    variant = relationship("ProductVariant", back_populates="cart_items")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(30), default="Confirmed")  # Confirmed, Processing, Shipped, Out for Delivery, Delivered, Cancelled
    subtotal_amount = Column(Float, nullable=False)
    shipping_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default="Credit/Debit Card")
    payment_status = Column(String(30), default="Paid")
    shipping_name = Column(String(100), nullable=False)
    shipping_email = Column(String(191), nullable=False)
    shipping_phone = Column(String(30), nullable=False)
    shipping_address = Column(Text, nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    shipping_country = Column(String(50), default="India")
    tracking_number = Column(String(100), nullable=True)
    estimated_delivery = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_name = Column(String(200), nullable=False)
    size = Column(String(20), nullable=False)
    color_name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    image_url = Column(String(500), nullable=True)

    order = relationship("Order", back_populates="items")

class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")
