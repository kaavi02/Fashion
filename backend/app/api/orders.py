from typing import List, Optional
from datetime import datetime, timedelta
import random
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.auth import get_current_user_optional, get_current_user
from backend.app.models.models import (
    User, Order, OrderItem, CartItem, ProductVariant, Product
)
from backend.app.schemas.schemas import (
    CheckoutRequest, OrderOut, OrderItemOut
)

router = APIRouter(prefix="", tags=["Orders & Checkout"])

def generate_order_number() -> str:
    timestamp = datetime.now().strftime("%y%m%d")
    random_digits = random.randint(1000, 9999)
    return f"VOGUE-{timestamp}-{random_digits}"

@router.post("/checkout/process", response_model=OrderOut)
def process_checkout(
    checkout_in: CheckoutRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Validates cart, checks stock availability, executes order creation,
    deducts stock inventory, and flushes cart.
    """
    # Fetch active cart items
    if current_user:
        cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    elif checkout_in.session_id:
        cart_items = db.query(CartItem).filter(CartItem.session_id == checkout_in.session_id).all()
    else:
        cart_items = []

    # If serverless ephemeral SQLite container lost cart rows, fallback to items in payload
    if not cart_items and checkout_in.items:
        for itm in checkout_in.items:
            var = db.query(ProductVariant).filter(ProductVariant.id == itm.variant_id).first()
            if var:
                cart_items.append(CartItem(
                    user_id=current_user.id if current_user else None,
                    session_id=checkout_in.session_id if not current_user else None,
                    variant_id=var.id,
                    quantity=itm.quantity
                ))

    if not cart_items:
        raise HTTPException(status_code=400, detail="Your shopping cart is empty")

    subtotal = 0.0
    items_to_create = []

    # Validate stock and calculate total
    for item in cart_items:
        variant = item.variant if hasattr(item, 'variant') and item.variant else db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
        if not variant:
            continue
        product = variant.product

        if variant.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Sorry, '{product.name} ({variant.size}/{variant.color_name})' only has {variant.stock_quantity} left in stock."
            )

        item_price = product.current_price
        subtotal += item_price * item.quantity

        items_to_create.append({
            "variant": variant,
            "product": product,
            "price": item_price,
            "quantity": item.quantity
        })

    shipping = 0.0 if subtotal >= 1999 else 149.0
    discount = 0.0
    total = subtotal + shipping - discount

    # Estimated delivery date (3-5 business days)
    est_date = (datetime.now() + timedelta(days=4)).strftime("%B %d, %Y")
    order_num = generate_order_number()
    tracking_num = f"TRK-{random.randint(10000000, 99999999)}"

    # Create Order
    order = Order(
        order_number=order_num,
        user_id=current_user.id if current_user else None,
        status="Confirmed",
        subtotal_amount=round(subtotal, 2),
        shipping_amount=round(shipping, 2),
        discount_amount=round(discount, 2),
        total_amount=round(total, 2),
        payment_method=checkout_in.payment_method,
        payment_status="Paid" if checkout_in.payment_method != "Cash on Delivery" else "Pending COD",
        shipping_name=checkout_in.shipping_name,
        shipping_email=checkout_in.shipping_email,
        shipping_phone=checkout_in.shipping_phone,
        shipping_address=checkout_in.shipping_address,
        shipping_city=checkout_in.shipping_city,
        shipping_state=checkout_in.shipping_state,
        shipping_postal_code=checkout_in.shipping_postal_code,
        shipping_country=checkout_in.shipping_country,
        tracking_number=tracking_num,
        estimated_delivery=est_date
    )
    db.add(order)
    db.flush()

    # Deduct stock and create OrderItems
    for data in items_to_create:
        variant = data["variant"]
        product = data["product"]
        variant.stock_quantity -= data["quantity"]

        order_item = OrderItem(
            order_id=order.id,
            variant_id=variant.id,
            product_id=product.id,
            product_name=product.name,
            size=variant.size,
            color_name=variant.color_name,
            price=data["price"],
            quantity=data["quantity"],
            image_url=product.image_url
        )
        db.add(order_item)

    # Empty the cart
    for item in cart_items:
        if getattr(item, 'id', None):
            db.delete(item)

    db.commit()
    db.refresh(order)
    return order

@router.get("/orders", response_model=List[OrderOut])
def get_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customer orders sorted newest first."""
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders

@router.get("/orders/{order_number_or_id}", response_model=OrderOut)
def get_order_detail(
    order_number_or_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve full details of an order by ID or order number."""
    if order_number_or_id.isdigit():
        order = db.query(Order).filter(Order.id == int(order_number_or_id)).first()
    else:
        order = db.query(Order).filter(Order.order_number == order_number_or_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # If authenticated, verify user owns the order (or user is admin)
    if current_user and not current_user.is_admin and order.user_id and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this order")

    return order
