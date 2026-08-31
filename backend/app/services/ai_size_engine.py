from typing import Dict, Any, Optional
import math

# Standard apparel sizing standards (centimeters)
SIZING_STANDARDS = {
    "men_tops": {
        "XS": {"chest": (84, 89), "waist": (70, 75), "sleeve": 81},
        "S":  {"chest": (90, 95), "waist": (76, 81), "sleeve": 83},
        "M":  {"chest": (96, 101), "waist": (82, 87), "sleeve": 85},
        "L":  {"chest": (102, 108), "waist": (88, 94), "sleeve": 88},
        "XL": {"chest": (109, 116), "waist": (95, 102), "sleeve": 90},
        "XXL": {"chest": (117, 126), "waist": (103, 112), "sleeve": 92}
    },
    "women_tops": {
        "XS": {"chest": (78, 83), "waist": (60, 65), "hips": (85, 90)},
        "S":  {"chest": (84, 89), "waist": (66, 71), "hips": (91, 96)},
        "M":  {"chest": (90, 95), "waist": (72, 77), "hips": (97, 102)},
        "L":  {"chest": (96, 102), "waist": (78, 84), "hips": (103, 109)},
        "XL": {"chest": (103, 110), "waist": (85, 92), "hips": (110, 117)},
        "XXL": {"chest": (111, 119), "waist": (93, 101), "hips": (118, 126)}
    },
    "bottoms": {
        "XS": {"waist": (68, 73), "hips": (86, 91), "inseam": 76},
        "S":  {"waist": (74, 79), "hips": (92, 97), "inseam": 78},
        "M":  {"waist": (80, 85), "hips": (98, 103), "inseam": 80},
        "L":  {"waist": (86, 92), "hips": (104, 109), "inseam": 82},
        "XL": {"waist": (93, 100), "hips": (110, 116), "inseam": 83},
        "XXL": {"waist": (101, 110), "hips": (117, 125), "inseam": 84}
    }
}

class AISizeRecommendationEngine:
    """
    Intelligent biometric apparel sizing engine.
    Calibrates body measurements, BMI, ease tolerance, and fit preference
    to predict the optimal garment size.
    """

    @classmethod
    def estimate_measurements(cls, gender: str, height_cm: float, weight_kg: float) -> Dict[str, float]:
        """
        Estimates chest, waist, and hip circumferences using empirical biometric anthropometry
        when exact tailor measurements are not provided.
        """
        gender_lower = (gender or "unisex").lower()
        bmi = weight_kg / ((height_cm / 100.0) ** 2)

        if "women" in gender_lower or "female" in gender_lower:
            chest = (0.47 * height_cm) + (0.39 * weight_kg)
            waist = (0.37 * height_cm) + (0.35 * weight_kg)
            hips = (0.52 * height_cm) + (0.45 * weight_kg)
        else:
            chest = (0.51 * height_cm) + (0.36 * weight_kg)
            waist = (0.43 * height_cm) + (0.37 * weight_kg)
            hips = (0.49 * height_cm) + (0.33 * weight_kg)

        return {
            "chest_cm": round(chest, 1),
            "waist_cm": round(waist, 1),
            "hips_cm": round(hips, 1),
            "bmi": round(bmi, 1)
        }

    @classmethod
    def predict_size(
        cls,
        gender: str = "unisex",
        height_cm: Optional[float] = None,
        weight_kg: Optional[float] = None,
        chest_cm: Optional[float] = None,
        waist_cm: Optional[float] = None,
        hips_cm: Optional[float] = None,
        preferred_fit: str = "regular",  # "tight", "regular", "loose"
        category_name: str = "Tops"
    ) -> Dict[str, Any]:
        """
        Evaluates body measurements against standard sizing distributions
        and returns recommended size, confidence score, and fit notes.
        """
        gender_clean = (gender or "unisex").lower()
        pref_fit_clean = (preferred_fit or "regular").lower()

        # Fill in missing metrics via anthropometric biometric estimation
        if (chest_cm is None or waist_cm is None or hips_cm is None) and (height_cm and weight_kg):
            est = cls.estimate_measurements(gender_clean, height_cm, weight_kg)
            chest_cm = chest_cm or est["chest_cm"]
            waist_cm = waist_cm or est["waist_cm"]
            hips_cm = hips_cm or est["hips_cm"]
            bmi = est["bmi"]
        elif height_cm and weight_kg:
            bmi = round(weight_kg / ((height_cm / 100.0) ** 2), 1)
        else:
            bmi = 22.0
            chest_cm = chest_cm or 96.0
            waist_cm = waist_cm or 82.0
            hips_cm = hips_cm or 98.0

        # Adjust effective measurements based on fit preference
        # "tight": wear size smaller/tighter tolerance
        # "loose": wear size roomier
        ease_adjustment = 0.0
        if pref_fit_clean in ["tight", "slim"]:
            ease_adjustment = -3.0
        elif pref_fit_clean in ["loose", "relaxed", "oversized"]:
            ease_adjustment = 3.5

        adjusted_chest = chest_cm + ease_adjustment
        adjusted_waist = waist_cm + ease_adjustment
        adjusted_hips = hips_cm + ease_adjustment

        # Select sizing matrix
        is_bottom = any(term in category_name.lower() for term in ["pant", "jean", "trousers", "bottom", "short"])
        is_women = "women" in gender_clean or "female" in gender_clean

        if is_bottom:
            chart = SIZING_STANDARDS["bottoms"]
            primary_key = "waist"
            user_metric = adjusted_waist
            raw_metric = waist_cm
        elif is_women:
            chart = SIZING_STANDARDS["women_tops"]
            primary_key = "chest"
            user_metric = adjusted_chest
            raw_metric = chest_cm
        else:
            chart = SIZING_STANDARDS["men_tops"]
            primary_key = "chest"
            user_metric = adjusted_chest
            raw_metric = chest_cm

        size_scores = {}
        ordered_sizes = ["XS", "S", "M", "L", "XL", "XXL"]

        for size_key, ranges in chart.items():
            min_val, max_val = ranges[primary_key]
            mid_val = (min_val + max_val) / 2.0
            distance = abs(user_metric - mid_val)
            
            # Confidence score inversely proportional to distance from midpoint
            # Maximum distance before score approaches 0 is ~15cm
            score = max(0.0, 100.0 - (distance * 6.5))
            size_scores[size_key] = round(score, 1)

        # Select highest scoring size
        best_size = max(size_scores, key=size_scores.get)
        confidence = size_scores[best_size]

        # Determine secondary alternative size
        best_idx = ordered_sizes.index(best_size)
        secondary_size = None
        secondary_reason = ""
        
        if pref_fit_clean in ["tight", "slim"] and best_idx > 0:
            secondary_size = ordered_sizes[best_idx - 1]
            secondary_reason = f"Size {secondary_size} for a figure-hugging, sculpted fit."
        elif pref_fit_clean in ["loose", "oversized"] and best_idx < len(ordered_sizes) - 1:
            secondary_size = ordered_sizes[best_idx + 1]
            secondary_reason = f"Size {secondary_size} for a modern oversized drape."
        elif best_idx < len(ordered_sizes) - 1 and user_metric > chart[best_size][primary_key][1] - 1:
            secondary_size = ordered_sizes[best_idx + 1]
            secondary_reason = f"Size {secondary_size} if you prefer slightly more room."
        elif best_idx > 0:
            secondary_size = ordered_sizes[best_idx - 1]
            secondary_reason = f"Size {secondary_size} if you prefer a tighter silhouette."

        # Generate personalized commentary
        fit_commentary = []
        if pref_fit_clean in ["loose", "oversized"]:
            fit_commentary.append("Tailored with relaxed ease around the chest and arms.")
        elif pref_fit_clean in ["tight", "slim"]:
            fit_commentary.append("Contoured for an athletic silhouette without bunching.")
        else:
            fit_commentary.append("Optimal proportion with natural drape and unrestricted movement.")

        if bmi < 18.5:
            fit_commentary.append("Slim frame profile: Recommended size prevents sleeve and shoulder excess.")
        elif bmi > 27.5:
            fit_commentary.append("Broad frame profile: Recommended size provides comfortable chest room.")

        # Dimension breakdown
        rec_range = chart[best_size][primary_key]
        return {
            "recommended_size": best_size,
            "confidence_score": min(98.0, max(82.0, confidence)),
            "fit_preference": pref_fit_clean.capitalize(),
            "secondary_size": secondary_size,
            "secondary_reason": secondary_reason,
            "user_metrics": {
                "chest_cm": chest_cm,
                "waist_cm": waist_cm,
                "hips_cm": hips_cm,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "bmi": bmi
            },
            "size_standard_range": f"{rec_range[0]} - {rec_range[1]} cm {primary_key}",
            "commentary": " ".join(fit_commentary),
            "size_scores": size_scores
        }
