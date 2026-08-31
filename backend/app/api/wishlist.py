from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.auth import get_current_user
from backend.app.models.models import User, WishlistItem, Product
from backend.app.schemas.schemas import WishlistToggleResponse, ProductListItem
from backend.app.api.products import format_product_list_item

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])

@router.get("", response_model=List[ProductListItem])
def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all products in customer's wishlist."""
    items = db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()
    products = [item.product for item in items if item.product]
    return [format_product_list_item(p) for p in products]

@router.post("/toggle/{product_id}", response_model=WishlistToggleResponse)
def toggle_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle a product in or out of the customer's wishlist."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == product_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return WishlistToggleResponse(
            product_id=product_id,
            in_wishlist=False,
            message="Removed from wishlist"
        )
    else:
        new_item = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.add(new_item)
        db.commit()
        return WishlistToggleResponse(
            product_id=product_id,
            in_wishlist=True,
            message="Added to wishlist"
        )
