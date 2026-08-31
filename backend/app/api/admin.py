from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.api.auth import get_current_user
from backend.app.models.models import (
    User, Order, OrderItem, Product, ProductVariant, Category, Brand
)

router = APIRouter(prefix="/admin", tags=["Admin Management"])

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensures the authenticated user has administrative privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Administrator privileges required."
        )
    return current_user

class StatusUpdatePayload(BaseModel):
    status: str

class StockUpdatePayload(BaseModel):
    stock: int = Field(ge=0)

class NewProductPayload(BaseModel):
    name: str
    category_id: int
    brand_id: int
    gender: str = "Unisex"
    base_price: float
    discount_price: Optional[float] = None
    image_url: str
    description: Optional[str] = None
    material: Optional[str] = "100% Premium Material"
    is_featured: bool = False
    size: str = "M"
    color_name: str = "Classic Black"
    color_hex: str = "#000000"
    stock_quantity: int = 10

@router.get("/overview")
def get_admin_overview(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Calculates live KPI metrics and summaries for store operations."""
    total_sales = db.query(func.sum(Order.total_amount)).scalar() or 0.0
    total_orders = db.query(Order).count()
    total_products = db.query(Product).count()
    total_customers = db.query(User).filter(User.is_admin == False).count()

    # Low stock variants (< 5 left)
    low_stock_count = db.query(ProductVariant).filter(ProductVariant.stock_quantity <= 4).count()

    # Recent orders
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(8).all()
    recent_orders_data = [
        {
            "id": o.id,
            "order_number": o.order_number,
            "customer_name": o.shipping_name,
            "customer_email": o.shipping_email,
            "total_amount": o.total_amount,
            "status": o.status,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else ""
        }
        for o in recent_orders
    ]

    # Status distribution
    status_counts = {}
    for st in ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]:
        status_counts[st] = db.query(Order).filter(Order.status == st).count()

    return {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_customers": total_customers,
        "low_stock_count": low_stock_count,
        "recent_orders": recent_orders_data,
        "status_counts": status_counts
    }

@router.get("/orders")
def get_all_orders(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Fetch all store orders with item details for fulfillment tracking."""
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    results = []
    for o in orders:
        items = [
            {
                "product_name": item.product_name,
                "size": item.size,
                "color_name": item.color_name,
                "price": item.price,
                "quantity": item.quantity,
                "item_total": item.item_total
            }
            for item in o.items
        ]
        results.append({
            "id": o.id,
            "order_number": o.order_number,
            "shipping_name": o.shipping_name,
            "shipping_email": o.shipping_email,
            "shipping_phone": o.shipping_phone,
            "shipping_address": o.shipping_address,
            "shipping_city": o.shipping_city,
            "total_amount": o.total_amount,
            "status": o.status,
            "payment_method": o.payment_method,
            "payment_status": o.payment_status,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "",
            "items": items
        })
    return results

@router.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: StatusUpdatePayload,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Updates order fulfillment status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return {"message": f"Order #{order.order_number} status updated to {order.status}", "status": order.status}

@router.get("/products")
def get_admin_products(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Fetch catalog products with variant stock details for inventory management."""
    products = db.query(Product).order_by(Product.id.desc()).all()
    results = []
    for p in products:
        variants = [
            {
                "id": v.id,
                "size": v.size,
                "color_name": v.color_name,
                "color_hex": v.color_hex,
                "stock_quantity": v.stock_quantity
            }
            for v in p.variants
        ]
        total_stock = sum(v.stock_quantity for v in p.variants)
        results.append({
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "category_name": p.category.name if p.category else "",
            "brand_name": p.brand.name if p.brand else "",
            "base_price": p.base_price,
            "current_price": p.current_price,
            "image_url": p.image_url,
            "is_featured": p.is_featured,
            "total_stock": total_stock,
            "variants": variants
        })
    return results

@router.patch("/variants/{variant_id}/stock")
def update_variant_stock(
    variant_id: int,
    payload: StockUpdatePayload,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update stock quantity for a specific variant."""
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    variant.stock_quantity = payload.stock
    db.commit()
    return {"message": "Stock updated successfully", "new_stock": variant.stock_quantity}

@router.post("/products")
def create_product(
    payload: NewProductPayload,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Add a new product to store catalog with default variant."""
    import re
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', payload.name.lower()).strip('-')
    existing = db.query(Product).filter(Product.slug == slug).first()
    if existing:
        import random
        slug = f"{slug}-{random.randint(100, 999)}"

    product = Product(
        name=payload.name,
        slug=slug,
        category_id=payload.category_id,
        brand_id=payload.brand_id,
        gender=payload.gender,
        base_price=payload.base_price,
        discount_price=payload.discount_price,
        image_url=payload.image_url,
        description=payload.description or f"Luxury {payload.name} crafted with fine materials.",
        material=payload.material,
        is_featured=payload.is_featured
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        size=payload.size,
        color_name=payload.color_name,
        color_hex=payload.color_hex,
        stock_quantity=payload.stock_quantity,
        sku=f"SKU-{product.id}-{payload.size}-{payload.color_name[:3].upper()}"
    )
    db.add(variant)
    db.commit()
    db.refresh(product)
    return {"message": "Product created successfully", "product_id": product.id, "slug": product.slug}

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete product from catalog."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.query(ProductVariant).filter(ProductVariant.product_id == product.id).delete()
    db.delete(product)
    db.commit()
    return {"message": "Product removed from catalog"}

@router.get("/users")
def get_customers(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List customer accounts."""
    users = db.query(User).order_by(User.id.desc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "phone": u.phone or "",
            "city": u.city or "",
            "is_admin": u.is_admin,
            "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else ""
        }
        for u in users
    ]
