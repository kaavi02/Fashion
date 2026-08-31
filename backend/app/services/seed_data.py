import json
import logging
from sqlalchemy.orm import Session
from backend.app.models.models import (
    User, UserMeasurement, Category, Brand, Product, ProductVariant
)
from backend.app.core.security import get_password_hash

logger = logging.getLogger("fashion_store")

def seed_initial_data(db: Session):
    """Idempotently populates database with fashion catalog, categories, brands, and demo accounts."""
    
    if db.query(Product).first() and db.query(User).filter(User.email == "demo@fashion.com").first():
        logger.info("Products and demo users already exist. Skipping seeding.")
        return

    logger.info("Seeding fashion catalog and demo accounts into database...")

    # 1. Categories
    category_definitions = [
        {"name": "Men's Apparel", "slug": "mens-apparel", "desc": "Contemporary shirts, tailored trousers, outerwear, and streetwear essentials for men.", "img": "https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?auto=format&fit=crop&w=800&q=80"},
        {"name": "Women's Collection", "slug": "womens-collection", "desc": "Elegant dresses, structured blazers, knitwear, and effortless chic silhouettes.", "img": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=800&q=80"},
        {"name": "Ethnic & Festive", "slug": "ethnic-festive", "desc": "Traditional elegance meets modern tailoring in kurtas, bandhgalas, and festive ensembles.", "img": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=800&q=80"},
        {"name": "Footwear & Sneakers", "slug": "footwear-sneakers", "desc": "Premium leather loafers, urban sneakers, and high-performance lifestyle kicks.", "img": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=800&q=80"},
        {"name": "Accessories & Bags", "slug": "accessories-bags", "desc": "Minimalist leather bags, designer sunglasses, premium belts, and timeless accents.", "img": "https://images.unsplash.com/photo-1523779917675-b6ed3a42a561?auto=format&fit=crop&w=800&q=80"},
    ]
    cat_map = {}
    for c in category_definitions:
        existing = db.query(Category).filter(Category.slug == c["slug"]).first()
        if not existing:
            cat = Category(name=c["name"], slug=c["slug"], description=c["desc"], image_url=c["img"])
            db.add(cat)
            db.flush()
            cat_map[c["slug"]] = cat.id
        else:
            cat_map[c["slug"]] = existing.id

    # 2. Brands
    brand_definitions = [
        {"name": "Zara", "slug": "zara", "desc": "High-fashion trends with European tailoring", "logo": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=200&q=80"},
        {"name": "Urban Vogue", "slug": "urban-vogue", "desc": "Modern minimalist streetwear with premium fabrications", "logo": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=200&q=80"},
        {"name": "Nike Sportswear", "slug": "nike", "desc": "Iconic athletic apparel and performance sneakers", "logo": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=200&q=80"},
        {"name": "Aura Luxe", "slug": "aura-luxe", "desc": "Haute couture silks, linens, and bespoke evening wear", "logo": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=200&q=80"},
        {"name": "Levi's Heritage", "slug": "levis", "desc": "Authentic denim mastery and American casual workwear", "logo": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=200&q=80"},
        {"name": "H&M Studio", "slug": "hm-studio", "desc": "Elevated seasonal collections with sustainable fabrics", "logo": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=200&q=80"}
    ]
    brand_map = {}
    for b in brand_definitions:
        existing = db.query(Brand).filter(Brand.slug == b["slug"]).first()
        if not existing:
            brand = Brand(name=b["name"], slug=b["slug"], description=b["desc"], logo_url=b["logo"])
            db.add(brand)
            db.flush()
            brand_map[b["slug"]] = brand.id
        else:
            brand_map[b["slug"]] = existing.id

    # 3. Products
    products_data = [
        {
            "name": "Relaxed Fit Cuban Collar Linen Shirt",
            "slug": "relaxed-fit-cuban-collar-linen-shirt",
            "description": "Crafted from 100% French flax linen, this breathable Cuban collar shirt features a laid-back silhouette, side vents, and pearlescent buttons. Perfect for warm evenings and resort styling.",
            "category_id": cat_map["mens-apparel"],
            "brand_id": brand_map["zara"],
            "gender": "Men",
            "base_price": 2990.0,
            "discount_price": 2490.0,
            "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=80",
            "additional_images": [
                "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=800&q=80"
            ],
            "material": "100% French Flax Linen",
            "care_instructions": "Machine wash cold delicate, hang dry in shade",
            "is_featured": True,
            "rating": 4.8,
            "reviews_count": 42,
            "variants": [
                {"size": "S", "color": "Sage Green", "hex": "#8A9A86", "stock": 15},
                {"size": "M", "color": "Sage Green", "hex": "#8A9A86", "stock": 25},
                {"size": "L", "color": "Sage Green", "hex": "#8A9A86", "stock": 20},
                {"size": "XL", "color": "Sage Green", "hex": "#8A9A86", "stock": 10},
                {"size": "M", "color": "Sand Dune", "hex": "#D7C9B8", "stock": 30}
            ]
        },
        {
            "name": "Oversized Heavyweight Cotton Graphic Tee",
            "slug": "oversized-heavyweight-cotton-graphic-tee",
            "description": "240 GSM organic ring-spun combed cotton. Boxy drop-shoulder cut featuring minimalist typography on chest and high-density rear graphic screen print.",
            "category_id": cat_map["mens-apparel"],
            "brand_id": brand_map["urban-vogue"],
            "gender": "Men",
            "base_price": 1890.0,
            "discount_price": 1490.0,
            "image_url": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=800&q=80",
            "additional_images": [],
            "material": "100% Organic Ring-spun Cotton 240 GSM",
            "care_instructions": "Wash inside out at 30°C",
            "is_featured": True,
            "rating": 4.9,
            "reviews_count": 88,
            "variants": [
                {"size": "S", "color": "Pitch Black", "hex": "#111111", "stock": 30},
                {"size": "M", "color": "Pitch Black", "hex": "#111111", "stock": 45},
                {"size": "L", "color": "Pitch Black", "hex": "#111111", "stock": 40},
                {"size": "M", "color": "Off White", "hex": "#FAF9F6", "stock": 25}
            ]
        },
        {
            "name": "Tailored Double-Breasted Wool Blazer",
            "slug": "tailored-double-breasted-wool-blazer",
            "description": "Sharp architectural tailoring with padded peak lapels, horn buttons, and full cupro lining. A statement outerwear piece that effortlessly crosses daytime smart into evening elegance.",
            "category_id": cat_map["womens-collection"],
            "brand_id": brand_map["aura-luxe"],
            "gender": "Women",
            "base_price": 8990.0,
            "discount_price": 7490.0,
            "image_url": "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=800&q=80",
            "additional_images": [],
            "material": "80% Virgin Wool, 20% Silk",
            "care_instructions": "Specialist dry clean only",
            "is_featured": True,
            "rating": 4.9,
            "reviews_count": 31,
            "variants": [
                {"size": "XS", "color": "Midnight Navy", "hex": "#1A2238", "stock": 8},
                {"size": "S", "color": "Midnight Navy", "hex": "#1A2238", "stock": 15},
                {"size": "M", "color": "Midnight Navy", "hex": "#1A2238", "stock": 18},
                {"size": "L", "color": "Midnight Navy", "hex": "#1A2238", "stock": 12}
            ]
        },
        {
            "name": "Pleated Slip Satin Midi Dress",
            "slug": "pleated-slip-satin-midi-dress",
            "description": "Fluid Japanese hammered satin cut on the bias to drape naturally around the body. Features delicate spaghetti straps and a subtle side slit for graceful movement.",
            "category_id": cat_map["womens-collection"],
            "brand_id": brand_map["zara"],
            "gender": "Women",
            "base_price": 4490.0,
            "discount_price": 3890.0,
            "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=800&q=80",
            "additional_images": [],
            "material": "100% Hammered Poly-Satin",
            "care_instructions": "Hand wash cold, iron low on reverse",
            "is_featured": True,
            "rating": 4.7,
            "reviews_count": 53,
            "variants": [
                {"size": "XS", "color": "Emerald Green", "hex": "#097969", "stock": 12},
                {"size": "S", "color": "Emerald Green", "hex": "#097969", "stock": 20},
                {"size": "M", "color": "Emerald Green", "hex": "#097969", "stock": 25},
                {"size": "L", "color": "Emerald Green", "hex": "#097969", "stock": 15}
            ]
        },
        {
            "name": "501 Original Fit Selvedge Denim Jeans",
            "slug": "501-original-fit-selvedge-denim-jeans",
            "description": "The quintessential straight-leg jean with signature button fly and red-line selvedge edge. Woven on traditional shuttle looms from premium 14oz heavyweight ring-spun cotton.",
            "category_id": cat_map["mens-apparel"],
            "brand_id": brand_map["levis"],
            "gender": "Men",
            "base_price": 5490.0,
            "discount_price": 4690.0,
            "image_url": "https://images.unsplash.com/photo-1542272604-780c96856592?auto=format&fit=crop&w=800&q=80",
            "additional_images": [],
            "material": "100% Selvedge Cotton 14oz",
            "care_instructions": "Wash cold once every 10 wears, hang dry",
            "is_featured": False,
            "rating": 4.9,
            "reviews_count": 112,
            "variants": [
                {"size": "30", "color": "Raw Indigo", "hex": "#1B2A4A", "stock": 14},
                {"size": "32", "color": "Raw Indigo", "hex": "#1B2A4A", "stock": 24},
                {"size": "34", "color": "Raw Indigo", "hex": "#1B2A4A", "stock": 20}
            ]
        },
        {
            "name": "Air Retro Low Top Leather Sneakers",
            "slug": "air-retro-low-top-leather-sneakers",
            "description": "Full-grain supple tumbled leather upper with perforated toe vamp, encapsulated Air cushion midsole, and durable rubber herringbone traction tread.",
            "category_id": cat_map["footwear-sneakers"],
            "brand_id": brand_map["nike"],
            "gender": "Unisex",
            "base_price": 8495.0,
            "discount_price": 7290.0,
            "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80",
            "additional_images": [],
            "material": "Tumbled Calf Leather & Air-Sole Unit",
            "care_instructions": "Wipe clean with damp cloth and leather protector",
            "is_featured": True,
            "rating": 4.9,
            "reviews_count": 164,
            "variants": [
                {"size": "8", "color": "Triple White", "hex": "#FFFFFF", "stock": 25},
                {"size": "9", "color": "Triple White", "hex": "#FFFFFF", "stock": 30},
                {"size": "10", "color": "Triple White", "hex": "#FFFFFF", "stock": 20}
            ]
        },
        {
            "name": "Embroidered Raw Silk Chanderi Kurta Set",
            "slug": "embroidered-raw-silk-chanderi-kurta-set",
            "description": "Exquisite hand-woven Chanderi silk with intricate thread embroidery on neckline and cuffs. Paired with tailored churidar trousers for celebrations and weddings.",
            "category_id": cat_map["ethnic-festive"],
            "brand_id": brand_map["aura-luxe"],
            "gender": "Men",
            "base_price": 7990.0,
            "discount_price": 6490.0,
            "image_url": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=800&q=80",
            "additional_images": [],
            "material": "Pure Handloom Chanderi Silk",
            "care_instructions": "Dry clean recommended",
            "is_featured": False,
            "rating": 4.8,
            "reviews_count": 27,
            "variants": [
                {"size": "S", "color": "Ivory Pearl", "hex": "#FDFBF7", "stock": 10},
                {"size": "M", "color": "Ivory Pearl", "hex": "#FDFBF7", "stock": 16},
                {"size": "L", "color": "Ivory Pearl", "hex": "#FDFBF7", "stock": 14}
            ]
        },
        {
            "name": "Minimalist Full Grain Leather Crossbody Bag",
            "slug": "minimalist-full-grain-leather-crossbody-bag",
            "description": "Vegetable-tanned Italian leather with hand-burnished edges, brushed brass hardware, magnetic flap closure, and an adjustable shoulder strap.",
            "category_id": cat_map["accessories-bags"],
            "brand_id": brand_map["urban-vogue"],
            "gender": "Unisex",
            "base_price": 4990.0,
            "discount_price": 3990.0,
            "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=800&q=80",
            "additional_images": [],
            "material": "Vegetable-Tanned Italian Leather",
            "care_instructions": "Treat with leather balsam every 6 months",
            "is_featured": False,
            "rating": 4.8,
            "reviews_count": 39,
            "variants": [
                {"size": "One Size", "color": "Cognac Brown", "hex": "#9A5B2D", "stock": 25},
                {"size": "One Size", "color": "Matte Black", "hex": "#1A1A1A", "stock": 30}
            ]
        }
    ]

    for p_info in products_data:
        existing = db.query(Product).filter(Product.slug == p_info["slug"]).first()
        if existing:
            continue
        variants_data = p_info.pop("variants")
        add_imgs = p_info.pop("additional_images", [])
        product = Product(
            **p_info,
            additional_images_json=json.dumps(add_imgs)
        )
        db.add(product)
        db.flush()

        for idx, var in enumerate(variants_data):
            variant = ProductVariant(
                product_id=product.id,
                size=var["size"],
                color_name=var["color"],
                color_hex=var["hex"],
                stock_quantity=var["stock"],
                sku=f"{product.slug[:8].upper()}-{var['size']}-{idx+1}"
            )
            db.add(variant)

    # 4. Users
    if not db.query(User).filter(User.email == "demo@fashion.com").first():
        demo_user = User(
            email="demo@fashion.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Alex Rivera",
            phone="+91 9876543210",
            address="Flat 402, Skyline Luxury Apartments, Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560038",
            country="India",
            is_admin=False
        )
        db.add(demo_user)
        db.flush()

        demo_measurements = UserMeasurement(
            user_id=demo_user.id,
            gender="men",
            height_cm=178.0,
            weight_kg=72.5,
            chest_cm=99.0,
            waist_cm=83.0,
            hips_cm=98.0,
            preferred_fit="regular"
        )
        db.add(demo_measurements)

    if not db.query(User).filter(User.email == "admin@fashion.com").first():
        admin_user = User(
            email="admin@fashion.com",
            hashed_password=get_password_hash("Admin123!"),
            full_name="Vogue Administrator",
            phone="+91 9876500000",
            address="Vogue Headquarters, Bandra West",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400050",
            country="India",
            is_admin=True
        )
        db.add(admin_user)

    db.commit()
    logger.info("Fashion catalog and demo users verified and seeded into MySQL!")
