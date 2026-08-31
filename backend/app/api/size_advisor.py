from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.auth import get_current_user_optional
from backend.app.models.models import User, UserMeasurement, Product
from backend.app.schemas.schemas import (
    SizeRecommendationRequest, SizeRecommendationResponse
)
from backend.app.services.ai_size_engine import AISizeRecommendationEngine

router = APIRouter(prefix="/size-advisor", tags=["AI Size Advisor"])

@router.post("/recommend", response_model=SizeRecommendationResponse)
def get_size_recommendation(
    req: SizeRecommendationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Intelligent AI sizing engine endpoint.
    Computes optimal size recommendation, fit confidence percentage,
    and personalized sizing commentary.
    """
    category_name = req.category_name or "Tops"
    gender = req.gender or "unisex"
    height_cm = req.height_cm
    weight_kg = req.weight_kg
    chest_cm = req.chest_cm
    waist_cm = req.waist_cm
    hips_cm = req.hips_cm
    preferred_fit = req.preferred_fit or "regular"

    # If product_id supplied, inherit category and gender from product
    if req.product_id:
        product = db.query(Product).filter(Product.id == req.product_id).first()
        if product:
            category_name = product.category.name if product.category else "Tops"
            gender = product.gender

    # If parameters missing and user logged in, use their saved measurements
    if current_user and (not height_cm or not weight_kg):
        saved_m = db.query(UserMeasurement).filter(UserMeasurement.user_id == current_user.id).first()
        if saved_m:
            height_cm = height_cm or saved_m.height_cm
            weight_kg = weight_kg or saved_m.weight_kg
            chest_cm = chest_cm or saved_m.chest_cm
            waist_cm = waist_cm or saved_m.waist_cm
            hips_cm = hips_cm or saved_m.hips_cm
            preferred_fit = preferred_fit or saved_m.preferred_fit
            gender = gender or saved_m.gender

    # Compute prediction
    result = AISizeRecommendationEngine.predict_size(
        gender=gender,
        height_cm=height_cm,
        weight_kg=weight_kg,
        chest_cm=chest_cm,
        waist_cm=waist_cm,
        hips_cm=hips_cm,
        preferred_fit=preferred_fit,
        category_name=category_name
    )

    # Save to user profile if requested
    if current_user and req.save_to_profile and (height_cm or chest_cm):
        meas = db.query(UserMeasurement).filter(UserMeasurement.user_id == current_user.id).first()
        if not meas:
            meas = UserMeasurement(
                user_id=current_user.id,
                gender=gender,
                height_cm=height_cm,
                weight_kg=weight_kg,
                chest_cm=chest_cm,
                waist_cm=waist_cm,
                hips_cm=hips_cm,
                preferred_fit=preferred_fit
            )
            db.add(meas)
        else:
            meas.gender = gender
            meas.height_cm = height_cm or meas.height_cm
            meas.weight_kg = weight_kg or meas.weight_kg
            meas.chest_cm = chest_cm or meas.chest_cm
            meas.waist_cm = waist_cm or meas.waist_cm
            meas.hips_cm = hips_cm or meas.hips_cm
            meas.preferred_fit = preferred_fit or meas.preferred_fit
        db.commit()

    return SizeRecommendationResponse(**result)

@router.get("/quick-check/{product_id}")
def quick_size_check(
    product_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Checks if current logged-in user has saved measurements,
    and returns immediate size recommendation for this product.
    """
    if not current_user:
        return {"has_measurements": False, "recommendation": None}

    meas = db.query(UserMeasurement).filter(UserMeasurement.user_id == current_user.id).first()
    if not meas or not meas.height_cm or not meas.weight_kg:
        return {"has_measurements": False, "recommendation": None}

    product = db.query(Product).filter(Product.id == product_id).first()
    cat_name = product.category.name if product and product.category else "Tops"
    gender = product.gender if product else meas.gender

    res = AISizeRecommendationEngine.predict_size(
        gender=gender,
        height_cm=meas.height_cm,
        weight_kg=meas.weight_kg,
        chest_cm=meas.chest_cm,
        waist_cm=meas.waist_cm,
        hips_cm=meas.hips_cm,
        preferred_fit=meas.preferred_fit,
        category_name=cat_name
    )

    return {
        "has_measurements": True,
        "recommendation": {
            "recommended_size": res["recommended_size"],
            "confidence_score": res["confidence_score"],
            "fit_preference": res["fit_preference"],
            "commentary": res["commentary"]
        }
    }
