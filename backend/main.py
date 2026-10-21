from __future__ import annotations

import base64
import cv2
import numpy as np
import json
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

APP_DIR = os.path.dirname(__file__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct").strip()

app = FastAPI(title="Food Verse AI API", version="1.0.0", description="Food intelligence project API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://food-verse-jj8dpiddd-food-verse-ai.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def preprocess_food_image(image_bytes: bytes) -> tuple[bytes, dict]:
    """Resize and normalize a food image before AI analysis."""
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file could not be decoded as an image.",
        )

    original_height, original_width = image.shape[:2]

    # Resize large images while preserving their aspect ratio.
    max_dimension = 1024
    scale = min(
        max_dimension / original_width,
        max_dimension / original_height,
        1.0,
    )

    if scale < 1.0:
        image = cv2.resize(
            image,
            (
                int(original_width * scale),
                int(original_height * scale),
            ),
            interpolation=cv2.INTER_AREA,
        )

    # Apply mild contrast normalization to improve visibility.
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lightness, channel_a, channel_b = cv2.split(lab)
    lightness = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    ).apply(lightness)
    normalized = cv2.merge((lightness, channel_a, channel_b))
    processed = cv2.cvtColor(normalized, cv2.COLOR_LAB2BGR)

    success, encoded_image = cv2.imencode(".jpg", processed)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Could not preprocess the uploaded image.",
        )

    metadata = {
        "original_width": original_width,
        "original_height": original_height,
        "processed_width": processed.shape[1],
        "processed_height": processed.shape[0],
    }

    return encoded_image.tobytes(), metadata
def get_groq_client():
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except Exception:
        return None


def ask_ai(prompt: str, image_bytes: bytes | None = None, mime_type: str = "image/jpeg") -> str | None:
    client = get_groq_client()
    if client is None:
        return None
    try:
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_bytes:
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}})
        result = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": content}],
            temperature=0.3,
            max_tokens=1200,
        )
        return result.choices[0].message.content or None
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {exc}") from exc


def parse_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return {"summary": cleaned}
        return {"summary": cleaned}


class RecipeRequest(BaseModel):
    ingredients: str = Field(min_length=2, max_length=1000)
    cuisine: str = "Any"
    servings: int = Field(default=2, ge=1, le=12)
    dietary_preferences: str = "None"


class MealPlanRequest(BaseModel):
    age: int = Field(default=20, ge=13, le=100)
    goal: str = "Balanced eating"
    diet: str = "Vegetarian"
    allergies: str = "None"
    meals_per_day: int = Field(default=4, ge=2, le=6)
    notes: str = ""


class HygieneRequest(BaseModel):
    observations: str = "General kitchen inspection"


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Food Verse AI", "ai_mode": "live" if GROQ_API_KEY else "demo"}


@app.post("/api/analyze-food")
async def analyze_food(
    file: UploadFile | None = File(default=None),
    context: str = Form(default=""),
):
    image_bytes = None
    mime_type = "image/jpeg"

    if file:
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Please upload an image file.",
            )

        image_bytes = await file.read()

        if len(image_bytes) > 8 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Please upload an image smaller than 8 MB.",
            )

        image_bytes, image_metadata = preprocess_food_image(image_bytes)
        mime_type = "image/jpeg"

    if image_bytes:
        prompt = f"""
Analyze this food photo.
Extra context: {context or 'none'}.

Return valid JSON only with these keys:
{{
  "dish_name": "identified food name",
  "calories_kcal": 250,
  "protein_g": 8,
  "carbs_g": 35,
  "fats_g": 9,
  "confidence_percent": 80,
  "health_score": 75,
  "health_label": "Moderately Healthy",
  "reasoning": "Explain the health score.",
  "description": "Brief food description.",
  "health_notes": "Nutritional observations.",
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}}

Requirements:
- Nutrition values are estimates, not exact measurements.
- health_score must be an integer from 0 to 100.
- health_label must be Healthy, Moderately Healthy,
  Less Healthy, or Uncertain.
- confidence_percent must be an integer from 0 to 100.
- Explain the score in reasoning.
- If identification is uncertain, explain why.
- Do not claim medical benefits.
"""

        answer = parse_json(
            ask_ai(prompt, image_bytes, mime_type)
        )

        if answer:
            answer["mode"] = "live AI"
            return answer

    return {
        "dish_name": "Sample vegetable poha",
        "calories_kcal": 280,
        "protein_g": 7,
        "carbs_g": 45,
        "fats_g": 8,
        "confidence_percent": 72,
        "health_score": 65,
        "health_label": "Moderately Healthy",
        "reasoning": (
            "Demo estimate based on a typical serving. "
            "Actual ingredients and portion size may change the score."
        ),
        "description": "Demo result; live AI analysis was unavailable.",
        "health_notes": (
            "Nutrition estimates vary with portion size and preparation."
        ),
        "suggestions": [
            "Add a protein source such as curd or roasted peanuts.",
            "Include fruit or vegetables for more variety.",
        ],
        "mode": "demo",
    }
async def freshness(file: UploadFile | None = File(default=None), storage: str = Form(default="Room temperature"), age: str = Form(default="Unknown")):
    image_bytes = None
    mime_type = "image/jpeg"
    if file:
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Please upload an image file.")
        image_bytes = await file.read()
        if len(image_bytes) > 8 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Please upload an image smaller than 8 MB.")
        mime_type = file.content_type or mime_type
    prompt = f"Inspect visible signs in this food photo. Storage: {storage}; time since purchase/preparation: {age}. Return JSON with item, visible_condition, risk_level (Low/Medium/High/Uncertain), visible_signs (array), recommendations (array), limitations. Do not certify food safety from an image."
    answer = parse_json(ask_ai(prompt, image_bytes, mime_type)) if image_bytes else None
    if answer:
        answer["mode"] = "live AI"
        return answer
    return {"item": "Sample produce", "visible_condition": "Unable to determine in demo mode", "risk_level": "Uncertain", "visible_signs": ["Demo response; no real image analysis was performed."], "recommendations": ["Check smell, texture, packaging and storage history.", "When in doubt, discard food that may be unsafe."], "limitations": "A photo cannot reliably establish food safety. Demo mode is active.", "mode": "demo"}


@app.post("/api/freshness")
async def freshness(
    file: UploadFile | None = File(default=None),
    storage: str = Form(default="Room temperature"),
    age: str = Form(default="Unknown"),
):
    if file is None:
        raise HTTPException(status_code=400, detail="Please upload a food image.")

    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")

    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Please upload an image smaller than 8 MB.",
        )

    image_bytes, image_metadata = preprocess_food_image(image_bytes)
    mime_type = "image/jpeg"

    prompt = f"""
Inspect visible signs in this food photo.
Storage condition: {storage}
Time since purchase or preparation: {age}

Return valid JSON with these keys:
item, visible_condition, risk_level, confidence_percent,
visible_signs (array), recommendations (array), limitations.

risk_level must be Low, Medium, High, or Uncertain.
confidence_percent must be an integer from 0 to 100.
Do not claim a photo can certify food safety.
Explain the limitations of visual inspection.
"""

    answer = parse_json(ask_ai(prompt, image_bytes, mime_type))

    if answer:
        answer["mode"] = "live AI"
        return answer

    return {
        "item": "Unknown food",
        "visible_condition": "Unable to determine",
        "risk_level": "Uncertain",
        "confidence_percent": 0,
        "visible_signs": ["Live analysis was unavailable."],
        "recommendations": [
            "Check smell, texture, and storage history.",
            "Discard food if you suspect it is unsafe.",
        ],
        "limitations": "A photo cannot reliably establish food safety.",
        "mode": "demo",
    }
@app.post("/api/recipe")
async def recipe(
    ingredients: str = Form(default=""),
    cuisine: str = Form(default="Indian"),
    servings: int = Form(default=2),
    dietary_preferences: str = Form(default="None"),
    file: UploadFile | None = File(default=None),
):
    image_bytes = None
    mime_type = "image/jpeg"

    if file:
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Please upload an image file.",
            )

        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded image is empty.",
            )

        if len(image_bytes) > 8 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Please upload an image smaller than 8 MB.",
            )

        image_bytes, image_metadata = preprocess_food_image(image_bytes)
        mime_type = "image/jpeg"

    if not ingredients.strip() and image_bytes is None:
        raise HTTPException(
            status_code=400,
            detail="Enter ingredients or upload an ingredient photo.",
        )

    prompt = f"""
Create a practical recipe.

Ingredients typed by the user: {ingredients or 'None provided'}
Cuisine: {cuisine}
Servings: {servings}
Dietary preferences: {dietary_preferences}

If an image is provided, identify visible ingredients from the image.
Use the typed ingredients and visible ingredients together when possible.
Do not claim certainty about ingredients that cannot be identified clearly.

Return valid JSON with these keys:
title, prep_minutes, cook_minutes, ingredients (array),
steps (array), tips (array).

Give clear quantities and step-by-step cooking instructions.
Respect the stated dietary preferences.
"""

    answer = parse_json(ask_ai(prompt, image_bytes, mime_type))

    if answer:
        answer["mode"] = "live AI"
        return answer

    return {
        "title": "Quick mixed-ingredient recipe",
        "prep_minutes": 10,
        "cook_minutes": 15,
        "ingredients": [
            item.strip()
            for item in ingredients.split(",")
            if item.strip()
        ] or ["Ingredients could not be identified from the image."],
        "steps": [
            "Wash and prepare the ingredients.",
            "Heat a little oil in a pan.",
            "Add ingredients according to their cooking time.",
            "Cook thoroughly, season to taste, and serve.",
        ],
        "tips": [
            "Check dietary restrictions before cooking.",
            "Confirm any ingredients identified from a photo.",
        ],
        "mode": "demo",
    }

@app.post("/api/meal-plan")
def meal_plan(request: MealPlanRequest):
    prompt = f"""
Create a general one-day meal plan for an adult.

Age: {request.age}
Goal: {request.goal}
Diet: {request.diet}
Allergies and restrictions: {request.allergies}
Meals per day: {request.meals_per_day}
Additional notes: {request.notes}

Return valid JSON with these keys:
title, disclaimer, daily_calories_estimate,
daily_macros_estimate, daily_meals, alternative_meals,
practical_tips.

daily_calories_estimate:
An approximate integer number of calories for the full day.

daily_macros_estimate:
An object containing approximate protein_g, carbs_g, and fats_g.

daily_meals:
An array of objects. Each object must contain:
meal, suggestions (array of strings), estimated_calories.

alternative_meals:
An array of objects with meal and alternatives (array of strings).
Provide practical alternatives for different preferences.

Requirements:
- Respect the specified diet and restrictions.
- Do not recommend foods that conflict with stated restrictions.
- Use realistic approximate nutrition estimates.
- Make clear that calorie and macronutrient values are estimates.
- Do not prescribe medical diets or claim exact nutritional values.
- Explain that individual needs vary by activity, health, and other factors.
"""

    answer = parse_json(ask_ai(prompt))

    if answer:
        answer["mode"] = "live AI"
        return answer

    return {
        "title": "Balanced one-day meal ideas",
        "disclaimer": (
            "Nutrition values are approximate. This is general information, "
            "not medical or dietetic advice."
        ),
        "daily_calories_estimate": None,
        "daily_macros_estimate": None,
        "daily_meals": [
            {
                "meal": "Breakfast",
                "suggestions": ["Vegetable poha or oats", "Milk or curd"],
                "estimated_calories": None,
            },
            {
                "meal": "Lunch",
                "suggestions": ["Roti or rice", "Dal and seasonal vegetables"],
                "estimated_calories": None,
            },
            {
                "meal": "Snack",
                "suggestions": ["Fruit", "A suitable snack"],
                "estimated_calories": None,
            },
            {
                "meal": "Dinner",
                "suggestions": ["Khichdi or roti with vegetables"],
                "estimated_calories": None,
            },
        ],
        "alternative_meals": [],
        "practical_tips": [
            "Adjust portions to your individual needs.",
            "Check ingredients carefully when allergies are present.",
        ],
        "mode": "demo",
    }

@app.post("/api/hygiene")
async def hygiene(file: UploadFile | None = File(default=None), observations: str = Form(default="General kitchen inspection")):
    image_bytes = None
    mime_type = "image/jpeg"
    if file:
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Please upload an image file.")
        image_bytes = await file.read()
        if len(image_bytes) > 8 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Please upload an image smaller than 8 MB.")
        image_bytes, image_metadata = preprocess_food_image(image_bytes)
        mime_type = "image/jpeg"
    prompt = f"""
Review this kitchen photo for visible hygiene indicators only.
Additional observations: {observations}.

Return valid JSON with these keys:
overall_status,
score_out_of_100,
observations (array),
violations (array),
suggested_actions (array),
limitations.

Check visible indicators such as:
- Cleanliness of counters and food preparation surfaces
- Handwashing facilities and visible hygiene practices
- Gloves and hair coverings when relevant
- Food separation and storage
- Visible contamination risks

For each violation, describe the visible issue and a suggested correction.
If no clear violation is visible, return an empty violations array.
score_out_of_100 must be a rough integer from 0 to 100, or null
if the image does not support a reasonable estimate.
Never claim regulatory compliance from a photo.

- Every item in violations must be a complete, meaningful string describing a visible issue and its corrective action.
- If no clear violation is visible, return an empty array: [].
- Never return empty strings, colons, or placeholder items in violations.
- Base all findings on the actual uploaded image. Do not invent damage, mold, dirt, or other hazards that are not clearly visible.
"""
    answer = parse_json(ask_ai(prompt, image_bytes, mime_type)) if image_bytes else None
    if answer:
        answer["mode"] = "live AI"
        return answer
    return {"overall_status": "Needs manual review", "score_out_of_100": None, "observations": ["Demo mode is active; no actual inspection was performed.", observations], "suggested_actions": ["Check handwashing, food separation, surface cleanliness and temperature logs.", "Document any issues and have a responsible person verify them."], "limitations": "This prototype is not a certified food-safety inspection tool.", "mode": "demo"}
