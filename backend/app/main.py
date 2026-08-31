import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, get_db, ACTIVE_DB_TYPE
from backend.app.services.seed_data import seed_initial_data
from backend.app.api import auth, products, cart, orders, wishlist, size_advisor
from backend.app.models.models import Category, Brand, Product

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

# Lifespan for initializing DB and seeding data
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Try to initialize schema and seed if writable
    try:
        Base.metadata.create_all(bind=engine)
        with Session(engine) as db:
            seed_initial_data(db)
    except Exception as exc:
        import logging
        logging.getLogger("fashion_store").warning(f"Startup DB init skipped: {exc}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Modern Fashion E-Commerce Store with AI Size Advisor, Full Catalog, and Cart",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Jinja2 Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(cart.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(wishlist.router, prefix=settings.API_V1_STR)
app.include_router(size_advisor.router, prefix=settings.API_V1_STR)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Handles browser favicon requests cleanly."""
    from fastapi import Response
    return Response(status_code=204)

@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint indicating active database engine status."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "database_backend": ACTIVE_DB_TYPE,
        "configured_host": settings.DB_HOST
    }

import time

_home_cache = None
_home_cache_time = 0
_pdp_cache = {}

# ----------------- Frontend HTML Routes -----------------

@app.get("/", response_class=HTMLResponse)
def page_home(request: Request, db: Session = Depends(get_db)):
    """Home landing page with hero, featured collections, and new arrivals (cached for high speed)."""
    global _home_cache, _home_cache_time
    now = time.time()
    if _home_cache and (now - _home_cache_time) < 60:
        categories, featured_products, brands = _home_cache
    else:
        categories = db.query(Category).filter(Category.is_active == True).all()
        featured_products = db.query(Product).filter(Product.is_featured == True).limit(8).all()
        brands = db.query(Brand).all()
        _home_cache = (categories, featured_products, brands)
        _home_cache_time = now

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Home",
            "categories": categories,
            "featured_products": featured_products,
            "brands": brands
        }
    )

@app.get("/products", response_class=HTMLResponse)
def page_products(request: Request):
    """Product catalog with live sidebar filters."""
    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "title": "Collection Catalog"
        }
    )

@app.get("/product/{slug}", response_class=HTMLResponse)
def page_product_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    """Product detail page with AI size recommender and variant selector (cached for high speed)."""
    now = time.time()
    if slug in _pdp_cache and (now - _pdp_cache[slug]["time"]) < 60:
        product = _pdp_cache[slug]["product"]
        related_products = _pdp_cache[slug]["related"]
    else:
        product = db.query(Product).filter(Product.slug == slug).first()
        if not product:
            return templates.TemplateResponse(
                request=request,
                name="404.html",
                context={"title": "Not Found"},
                status_code=404
            )
        
        related_products = db.query(Product).filter(
            Product.category_id == product.category_id,
            Product.id != product.id
        ).limit(4).all()
        _pdp_cache[slug] = {"product": product, "related": related_products, "time": now}

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "title": product.name,
            "product": product,
            "related_products": related_products
        }
    )

@app.get("/cart", response_class=HTMLResponse)
def page_cart(request: Request):
    """Shopping bag and cost breakdown page."""
    return templates.TemplateResponse(
        request=request,
        name="cart.html",
        context={
            "title": "Shopping Bag"
        }
    )

@app.get("/checkout", response_class=HTMLResponse)
def page_checkout(request: Request):
    """Checkout page with shipping address and payment method."""
    return templates.TemplateResponse(
        request=request,
        name="checkout.html",
        context={
            "title": "Checkout"
        }
    )

@app.get("/orders", response_class=HTMLResponse)
def page_orders(request: Request):
    """Order history and tracking page."""
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={
            "title": "My Orders & Tracking"
        }
    )

@app.get("/wishlist", response_class=HTMLResponse)
def page_wishlist(request: Request):
    """Wishlist page."""
    return templates.TemplateResponse(
        request=request,
        name="wishlist.html",
        context={
            "title": "Saved Wishlist"
        }
    )

@app.get("/profile", response_class=HTMLResponse)
def page_profile(request: Request):
    """Customer profile and AI measurement management page."""
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "title": "My Profile & AI Sizing Profile"
        }
    )

@app.get("/login", response_class=HTMLResponse)
def page_login(request: Request):
    """Customer login page."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "title": "Sign In"
        }
    )

@app.get("/register", response_class=HTMLResponse)
def page_register(request: Request):
    """Customer registration page."""
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "title": "Create Account"
        }
    )
