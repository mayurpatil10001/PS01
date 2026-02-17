"""Synthetic data generator for training ML models.

Generates realistic 2-year historical data for 15 Indian rural villages
with embedded outbreak patterns, seasonal variations, and water quality trends.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random


# Village data with real coordinates
VILLAGES = [
    {"id": "MH_SHP", "name": "Shirpur", "lat": 21.3500, "lon": 74.8800, "pop": 28000, "state": "Maharashtra"},
    {"id": "MH_DHA", "name": "Dharangaon", "lat": 21.0167, "lon": 75.2667, "pop": 15000, "state": "Maharashtra"},
    {"id": "MH_SHA", "name": "Shahada", "lat": 21.5452, "lon": 74.4695, "pop": 22000, "state": "Maharashtra"},
    {"id": "MH_RAV", "name": "Raver", "lat": 21.2456, "lon": 76.0423, "pop": 18000, "state": "Maharashtra"},
    {"id": "MH_YAW", "name": "Yawal", "lat": 21.1667, "lon": 75.7000, "pop": 12000, "state": "Maharashtra"},
    {"id": "MH_CHO", "name": "Chopda", "lat": 21.2500, "lon": 75.3000, "pop": 25000, "state": "Maharashtra"},
    {"id": "MH_AMA", "name": "Amalner", "lat": 21.0500, "lon": 75.0667, "pop": 31000, "state": "Maharashtra"},
    {"id": "MH_PAR", "name": "Parola", "lat": 20.8833, "lon": 75.1167, "pop": 14000, "state": "Maharashtra"},
    {"id": "MH_PAC", "name": "Pachora", "lat": 20.6572, "lon": 75.3444, "pop": 19000, "state": "Maharashtra"},
    {"id": "MH_CHA", "name": "Chalisgaon", "lat": 20.4619, "lon": 75.0167, "pop": 42000, "state": "Maharashtra"},
    {"id": "UP_BAH", "name": "Bahraich", "lat": 27.5700, "lon": 81.5900, "pop": 55000, "state": "UP"},
    {"id": "UP_BAL", "name": "Balrampur", "lat": 27.4300, "lon": 82.1800, "pop": 38000, "state": "UP"},
    {"id": "UP_SHR", "name": "Shravasti", "lat": 27.5200, "lon": 81.8700, "pop": 21000, "state": "UP"},
    {"id": "UP_LAK", "name": "Lakhimpur", "lat": 27.9500, "lon": 80.7800, "pop": 47000, "state": "UP"},
    {"id": "UP_GON", "name": "Gonda", "lat": 27.1300, "lon": 81.9700, "pop": 62000, "state": "UP"}
]


def generate_training_data() -> pd.DataFrame:
    """Generate 2 years of synthetic training data for all villages."""
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range = pd.date_range(start_date, end_date, freq='D')
    
    all_data = []
    
    for village in VILLAGES:
        village_id = village["id"]
        village_name = village["name"]
        population = village["pop"]
        
        for date in date_range:
            month = date.month
            day_of_year = date.timetuple().tm_yday
            
            # Seasonal multipliers
            if 6 <= month <= 9:  # Monsoon
                seasonal_risk = 1.8
                rainfall_mm = np.random.gamma(5, 15)
            elif 3 <= month <= 5:  # Summer
                seasonal_risk = 1.3
                rainfall_mm = np.random.gamma(2, 3)
            elif month >= 11 or month <= 2:  # Winter
                seasonal_risk = 0.7
                rainfall_mm = np.random.gamma(1, 2)
            else:  # Post-monsoon
                seasonal_risk = 1.1
                rainfall_mm = np.random.gamma(3, 5)
            
            # Base water quality (varies by village)
            base_ph = 7.0 + np.random.normal(0, 0.3)
            base_turbidity = 2.0 + np.random.gamma(2, 0.5)
            base_tds = 350 + np.random.normal(0, 50)
            base_coliform = 5 + np.random.gamma(2, 2)
            
            # Apply seasonal effects
            turbidity = base_turbidity * seasonal_risk
            coliform = base_coliform * seasonal_risk
            
            # Embedded outbreak patterns
            is_outbreak = False
            outbreak_type = "none"
            
            # Shirpur cholera outbreak: Aug 2024
            if village_id == "MH_SHP" and date.year == 2024 and date.month == 8:
                days_into_outbreak = date.day
                if days_into_outbreak <= 20:
                    is_outbreak = True
                    outbreak_type = "cholera"
                    # Gradual water quality decline before outbreak
                    turbidity *= (1 + days_into_outbreak * 0.15)
                    coliform *= (1 + days_into_outbreak * 0.2)
                    base_ph -= days_into_outbreak * 0.02
            
            # Bahraich typhoid outbreak: Sep 2024
            if village_id == "UP_BAH" and date.year == 2024 and date.month == 9:
                days_into_outbreak = date.day
                if days_into_outbreak <= 18:
                    is_outbreak = True
                    outbreak_type = "typhoid"
                    turbidity *= (1 + days_into_outbreak * 0.12)
                    coliform *= (1 + days_into_outbreak * 0.18)
                    base_tds += days_into_outbreak * 10
            
            # Symptom counts
            if is_outbreak:
                if outbreak_type == "cholera":
                    diarrhea = int(np.random.gamma(10, 3))
                    vomiting = int(np.random.gamma(7, 2))
                    fever = int(np.random.gamma(5, 2))
                    abdominal_pain = int(np.random.gamma(6, 2))
                    blood_in_stool = int(np.random.gamma(2, 1))
                elif outbreak_type == "typhoid":
                    diarrhea = int(np.random.gamma(6, 2))
                    vomiting = int(np.random.gamma(4, 2))
                    fever = int(np.random.gamma(8, 3))
                    abdominal_pain = int(np.random.gamma(7, 2))
                    blood_in_stool = int(np.random.gamma(1, 0.5))
            else:
                # Baseline symptoms (normal background)
                diarrhea = int(np.random.poisson(population * 0.0001))
                vomiting = int(np.random.poisson(population * 0.00005))
                fever = int(np.random.poisson(population * 0.0002))
                abdominal_pain = int(np.random.poisson(population * 0.00008))
                blood_in_stool = int(np.random.poisson(population * 0.00001))
            
            # Calculate features
            symptom_score = (diarrhea * 3 + vomiting * 2 + fever * 2 + 
                           abdominal_pain * 1 + blood_in_stool * 4) / population * 1000
            
            ph_deviation = abs(base_ph - 7.0)
            chlorine_deficit = max(0, 0.5 - np.random.gamma(0.5, 0.2))
            coliform_normalized = min(100, coliform * 2)
            
            water_quality_index = 100 - (ph_deviation * 10 + turbidity * 5 + 
                                        coliform_normalized * 30 + chlorine_deficit * 15)
            water_quality_index = max(0, min(100, water_quality_index))
            
            temp_anomaly = abs(25 - (20 + np.random.normal(5, 3)))
            flood_risk = 1 if rainfall_mm > 50 else 0
            environmental_risk = rainfall_mm * 0.3 + temp_anomaly * 0.2 + flood_risk * 0.5
            
            # Total cases
            total_cases = diarrhea + vomiting + fever
            
            # Alert level
            if symptom_score > 15 or water_quality_index < 30:
                alert_level = "critical"
            elif symptom_score > 10 or water_quality_index < 50:
                alert_level = "high"
            elif symptom_score > 5 or water_quality_index < 65:
                alert_level = "medium"
            elif symptom_score > 2 or water_quality_index < 75:
                alert_level = "low"
            else:
                alert_level = "baseline"
            
            # Risk score (0-100)
            risk_score = min(100, symptom_score * 3 + (100 - water_quality_index) * 0.5 + 
                           environmental_risk * 2)
            
            record = {
                "date": date,
                "village_id": village_id,
                "village_name": village_name,
                "population": population,
                "diarrhea_cases": diarrhea,
                "vomiting_cases": vomiting,
                "fever_cases": fever,
                "abdominal_pain_cases": abdominal_pain,
                "blood_in_stool_cases": blood_in_stool,
                "total_cases": total_cases,
                "ph_level": round(base_ph, 2),
                "turbidity_ntu": round(turbidity, 2),
                "tds_ppm": round(base_tds, 1),
                "coliform_cfu": round(coliform, 1),
                "chlorine_ppm": round(max(0, 0.5 - chlorine_deficit), 2),
                "rainfall_mm": round(rainfall_mm, 1),
                "temperature_celsius": round(25 + np.random.normal(0, 5), 1),
                "symptom_score": round(symptom_score, 2),
                "water_quality_index": round(water_quality_index, 1),
                "environmental_risk": round(environmental_risk, 2),
                "risk_score": round(risk_score, 1),
                "alert_level": alert_level,
                "disease_type": outbreak_type,
                "is_outbreak": is_outbreak
            }
            
            all_data.append(record)
    
    df = pd.DataFrame(all_data)
    
    # Add lag features
    for village_id in df['village_id'].unique():
        village_mask = df['village_id'] == village_id
        df.loc[village_mask, 'lag_1_cases'] = df.loc[village_mask, 'total_cases'].shift(1).fillna(0)
        df.loc[village_mask, 'lag_3_cases'] = df.loc[village_mask, 'total_cases'].shift(3).fillna(0)
        df.loc[village_mask, 'lag_7_cases'] = df.loc[village_mask, 'total_cases'].shift(7).fillna(0)
        df.loc[village_mask, 'rolling_7day_case_rate'] = df.loc[village_mask, 'total_cases'].rolling(7, min_periods=1).mean()
    
    return df


def get_village_data() -> list[dict]:
    """Get village metadata."""
    return VILLAGES
