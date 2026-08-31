from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from backend.app.core.database import get_db
from backend.app.models.models import Product, ProductVariant, Category, Brand
from backend.app.schemas.schemas import (
    ProductListItem, ProductDetail, CategoryOut, BrandOut, VariantOut
)

router = APIRouter(prefix="/products", tags=["Products & Catalog"])

def format_product_list_item(p: Product) -> ProductListItem:
    """Helper to convert Product ORM object into high-level ProductListItem."""
    sizes = sorted(list({v.size for v in p.variants if v.stock_quantity > 0}))
    
    # Unique colors preserving hex
    colors_seen = set()
    colors = []
    for v in p.variants:
        if v.color_name not in colors_seen and v.stock_quantity > 0:
            colors_seen.add(v.color_name)
            colors.append({"name": v.color_name, "hex": v.color_hex})

    return ProductListItem(
        id=p.id,
        name=p.name,
        slug=p.slug,
        description=p.description,
        base_price=p.base_price,
        discount_price=p.discount_price,
        current_price=p.current_price,
        discount_percent=p.discount_percent,
        image_url=p.image_url,
        gender=p.gender,
        rating=p.rating,
        reviews_count=p.reviews_count,
        is_featured=p.is_featured,
        category_name=p.category.name if p.category else "",
        brand_name=p.brand.name if p.brand else "",
        available_sizes=sizes,
        available_colors=colors
    )

@router.get("", response_model=List[ProductListItem])
def list_products(
    category: Optional[str] = Query(None, description="Category slug or name"),
    brand: Optional[str] = Query(None, description="Brand slug or name"),
    size: Optional[str] = Query(None, description="Filter by variant size"),
    color: Optional[str] = Query(None, description="Filter by variant color"),
    gender: Optional[str] = Query(None, description="Men, Women, or Unisex"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    search: Optional[str] = Query(None, description="Search keyword in title or description"),
    sort: Optional[str] = Query("popular", description="Sort order: popular, price_asc, price_desc, newest"),
    featured: Optional[bool] = Query(None, description="Filter featured products only"),
    db: Session = Depends(get_db)
):
    """
    Search and filter fashion catalog by category, brand, size, color, price range, and gender.
    """
    query = db.query(Product).join(Product.category).join(Product.brand)

    if category:
        query = query.filter(or_(Category.slug == category, Category.name.ilike(f"%{category}%")))

    if brand:
        query = query.filter(or_(Brand.slug == brand, Brand.name.ilike(f"%{brand}%")))

    if gender:
        query = query.filter(Product.gender.ilike(gender))

    if featured is not None:
        query = query.filter(Product.is_featured == featured)

    if search:
        kw = f"%{search}%"
        query = query.filter(or_(Product.name.ilike(kw), Product.description.ilike(kw)))

    if min_price is not None:
        query = query.filter(
            func.coalesce(Product.discount_price, Product.base_price) >= min_price
        )

    if max_price is not None:
        query = query.filter(
            func.coalesce(Product.discount_price, Product.base_price) <= max_price
        )

    if size or color:
        query = query.join(Product.variants)
        if size:
            query = query.filter(ProductVariant.size == size)
        if color:
            query = query.filter(ProductVariant.color_name.ilike(f"%{color}%"))
        query = query.distinct()

    # Sorting
    if sort == "price_asc":
        query = query.order_by(func.coalesce(Product.discount_price, Product.base_price).asc())
    elif sort == "price_desc":
        query = query.order_by(func.coalesce(Product.discount_price, Product.base_price).desc())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    else:  # popular / rating
        query = query.order_by(Product.rating.desc(), Product.reviews_count.desc())

    products = query.all()
    return [format_product_list_item(p) for p in products]

import time

_filters_cache = None
_filters_cache_time = 0
CACHE_TTL = 120  # 2 minutes

@router.get("/filters")
def get_available_filters(db: Session = Depends(get_db)):
    """Retrieves all distinct available filter values (cached for ultra-fast performance)."""
    global _filters_cache, _filters_cache_time
    now = time.time()
    if _filters_cache and (now - _filters_cache_time) < CACHE_TTL:
        return _filters_cache

    sizes_res = db.query(ProductVariant.size).distinct().all()
    sizes = [s[0] for s in sizes_res if s[0]]

    # Ordered sizes
    size_order = ["XS", "S", "M", "L", "XL", "XXL", "30", "32", "34", "36", "7", "8", "9", "10", "One Size"]
    sorted_sizes = sorted(sizes, key=lambda x: size_order.index(x) if x in size_order else 999)

    colors_res = db.query(ProductVariant.color_name, ProductVariant.color_hex).distinct().all()
    colors = [{"name": c[0], "hex": c[1]} for c in colors_res if c[0]]

    price_stats = db.query(
        func.min(Product.base_price),
        func.max(Product.base_price)
    ).first()

    categories = db.query(Category).filter(Category.is_active == True).all()
    brands = db.query(Brand).all()

    _filters_cache = {
        "sizes": sorted_sizes,
        "colors": colors,
        "min_price": float(price_stats[0] or 0),
        "max_price": float(price_stats[1] or 15000),
        "categories": [CategoryOut.model_validate(c) for c in categories],
        "brands": [BrandOut.model_validate(b) for b in brands]
    }
    _filters_cache_time = now
    return _filters_cache

@router.get("/{slug_or_id}", response_model=ProductDetail)
def get_product(slug_or_id: str, db: Session = Depends(get_db)):
    """Get single product detailed specifications, images, and live variant inventory."""
    if slug_or_id.isdigit():
        product = db.query(Product).filter(Product.id == int(slug_or_id)).first()
    else:
        product = db.query(Product).filter(Product.slug == slug_or_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductDetail(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        base_price=product.base_price,
        discount_price=product.discount_price,
        current_price=product.current_price,
        discount_percent=product.discount_percent,
        image_url=product.image_url,
        additional_images=product.additional_images,
        material=product.material,
        care_instructions=product.care_instructions,
        gender=product.gender,
        rating=product.rating,
        reviews_count=product.reviews_count,
        is_featured=product.is_featured,
        category=CategoryOut.model_validate(product.category),
        brand=BrandOut.model_validate(product.brand),
        variants=[VariantOut.model_validate(v) for v in product.variants]
    )
