from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.auth import get_current_user_optional
from backend.app.models.models import User, CartItem, ProductVariant, Product
from backend.app.schemas.schemas import (
    CartItemAdd, CartItemUpdate, CartItemOut, CartSummary
)

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])

def get_cart_query(db: Session, user: Optional[User], session_id: Optional[str]):
    """Helper to query cart items by user_id or guest session_id."""
    if user:
        return db.query(CartItem).filter(CartItem.user_id == user.id)
    elif session_id:
        return db.query(CartItem).filter(CartItem.session_id == session_id)
    else:
        return db.query(CartItem).filter(False)

def build_cart_summary(items) -> CartSummary:
    formatted_items = []
    subtotal = 0.0

    for item in items:
        variant = item.variant
        product = variant.product
        price = product.current_price
        item_total = price * item.quantity
        subtotal += item_total

        formatted_items.append(CartItemOut(
            id=item.id,
            variant_id=variant.id,
            product_id=product.id,
            product_name=product.name,
            product_slug=product.slug,
            image_url=product.image_url,
            size=variant.size,
            color_name=variant.color_name,
            color_hex=variant.color_hex,
            price=price,
            quantity=item.quantity,
            item_total=round(item_total, 2),
            stock_quantity=variant.stock_quantity
        ))

    shipping = 0.0 if (subtotal >= 1999 or subtotal == 0) else 149.0
    discount = 0.0
    total = subtotal + shipping - discount
    total_count = sum(i.quantity for i in items)

    return CartSummary(
        items=formatted_items,
        subtotal=round(subtotal, 2),
        shipping=round(shipping, 2),
        discount=round(discount, 2),
        total=round(total, 2),
        total_count=total_count
    )

@router.get("", response_model=CartSummary)
def get_cart(
    session_id: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Retrieve shopping cart contents, calculations, and items."""
    # If user just logged in and has guest cart session, associate guest cart items to user
    if current_user and session_id:
        guest_items = db.query(CartItem).filter(CartItem.session_id == session_id).all()
        for g_item in guest_items:
            existing = db.query(CartItem).filter(
                CartItem.user_id == current_user.id,
                CartItem.variant_id == g_item.variant_id
            ).first()
            if existing:
                existing.quantity += g_item.quantity
                db.delete(g_item)
            else:
                g_item.user_id = current_user.id
                g_item.session_id = None
        db.commit()

    items = get_cart_query(db, current_user, session_id).all()
    return build_cart_summary(items)

@router.post("/add", response_model=CartSummary)
def add_to_cart(
    item_in: CartItemAdd,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Add selected garment variant to cart with stock validation."""
    variant = db.query(ProductVariant).filter(ProductVariant.id == item_in.variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Selected product variant does not exist")

    if variant.stock_quantity <= 0:
        raise HTTPException(status_code=400, detail="This size/color combination is currently out of stock")

    # Check if item already in cart
    if current_user:
        existing = db.query(CartItem).filter(
            CartItem.user_id == current_user.id,
            CartItem.variant_id == item_in.variant_id
        ).first()
    elif item_in.session_id:
        existing = db.query(CartItem).filter(
            CartItem.session_id == item_in.session_id,
            CartItem.variant_id == item_in.variant_id
        ).first()
    else:
        raise HTTPException(status_code=400, detail="Session ID or authentication required")

    requested_qty = item_in.quantity
    if existing:
        new_qty = existing.quantity + requested_qty
        if new_qty > variant.stock_quantity:
            new_qty = variant.stock_quantity
        existing.quantity = new_qty
    else:
        if requested_qty > variant.stock_quantity:
            requested_qty = variant.stock_quantity
        new_item = CartItem(
            user_id=current_user.id if current_user else None,
            session_id=item_in.session_id if not current_user else None,
            variant_id=item_in.variant_id,
            quantity=requested_qty
        )
        db.add(new_item)

    db.commit()
    items = get_cart_query(db, current_user, item_in.session_id).all()
    return build_cart_summary(items)

@router.put("/{cart_item_id}", response_model=CartSummary)
def update_cart_item(
    cart_item_id: int,
    item_in: CartItemUpdate,
    session_id: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Adjust quantity of item in cart."""
    item = db.query(CartItem).filter(CartItem.id == cart_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if item_in.quantity <= 0:
        db.delete(item)
    else:
        if item_in.quantity > item.variant.stock_quantity:
            raise HTTPException(status_code=400, detail=f"Only {item.variant.stock_quantity} available in stock")
        item.quantity = item_in.quantity

    db.commit()
    items = get_cart_query(db, current_user, session_id).all()
    return build_cart_summary(items)

@router.delete("/{cart_item_id}", response_model=CartSummary)
def remove_cart_item(
    cart_item_id: int,
    session_id: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Delete an item from cart."""
    item = db.query(CartItem).filter(CartItem.id == cart_item_id).first()
    if item:
        db.delete(item)
        db.commit()

    items = get_cart_query(db, current_user, session_id).all()
    return build_cart_summary(items)

@router.post("/clear", response_model=CartSummary)
def clear_cart(
    session_id: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Clear all items in current cart."""
    query = get_cart_query(db, current_user, session_id)
    query.delete()
    db.commit()
    return build_cart_summary([])
