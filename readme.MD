# Safetify — System Architecture & ML Pipeline Documentation

## 1. Overall Architecture

```
React Native
      │
      ▼
Node.js + Express
      │
      ├────────► Google Directions API
      │
      ├────────► MySQL / Firebase
      │
      └────────► Python ML API (FastAPI)
                    │
                    ▼
             Risk Analysis Engine
```

- **React Native** শুধুমাত্র UI।
- **Express** পুরো application-এর brain।
- **Python** শুধুমাত্র ML এবং Crime Risk Analysis করে।

---

## 2. Dataset

Bangladesh Crime Dataset-এ গুরুত্বপূর্ণ field ছিল:

| Feature | Purpose |
|---|---|
| `latitude` | Crime location |
| `longitude` | Crime location |
| `incident_weekday` | কোন দিনে crime হয়েছে |
| `part_of_the_day` | Morning / Night / Evening |
| `crime` | Crime type |
| `incident_district` | Area |
| `weather` / `population` | Dataset-এ ছিল, কিন্তু বর্তমানে model-এ ব্যবহার করা হচ্ছে না |

শেষ পর্যন্ত model train করার জন্য ব্যবহৃত features:

- `latitude`
- `longitude`
- `incident_weekday`
- `part_of_the_day`

**Target (y):** `crime_count`

---

## 3. DBSCAN কেন ব্যবহার করা হয়েছে?

DBSCAN supervised model না — এটা একটি **Hotspot Discovery Algorithm**।

**Input:**
- Latitude
- Longitude

**Output:**
- Cluster 0
- Cluster 1
- Cluster 2
- ...

এতে nearby crime location গুলো একসাথে group হয়। এরপর প্রতিটি cluster থেকে বের করা হয়েছে:

- Centroid
- Crime count
- Dominant crime
- Dominant day
- Dominant time

এই তথ্যগুলো `hotspots.csv`-এ সংরক্ষিত আছে।

---

## 4. BallTree কেন?

DBSCAN training-এর পরে runtime-এ প্রতি request-এ DBSCAN চালানো সম্ভব না। তাই **BallTree** তৈরি করা হয়েছে — এটি একটি spatial search index।

**Example:**

User Location → `23.774569, 90.355292`

BallTree instantly বের করে দেয় — 300 মিটারের মধ্যে কোন কোন incident আছে।

**Time Complexity:**

| Method | Complexity |
|---|---|
| Naive Search | O(n) |
| BallTree | O(log n) |

এই কারণে FastAPI খুব দ্রুত response দেয়।

---

## 5. Random Forest Model

এটাই মূল ML model।

**Training Features:**
- Latitude
- Longitude
- Weekday
- Part of Day

**Target:**
- Crime Count

Model predict করে: **Estimated Crime Count**

**Example:**

| Input | Value |
|---|---|
| Lat | — |
| Lon | — |
| Weekday | Wednesday |
| Part of Day | Morning |

**Output:** `1.21`

মানে, এই location-এ, এই weekday-তে, এই সময়ে — historically প্রায় **1.21 incident** হওয়ার pattern দেখা গেছে।

> এটা probability না, Crime Type না, Risk Percentage না — এটি একটি **expected crime occurrence estimate**।

---

## 6. Historical Analysis

শুধু ML prediction ব্যবহার করা হচ্ছে না — প্রথমে historical analysis করা হয়।

**Function:** `calculate_point_risk()`

এই function-এ:

1. BallTree থেকে nearby incident বের করা হয়।
2. তারপর filter করা হয়:
   - Weekday
   - Part of day
3. তারপর calculate করা হয়:

### Incident Count
Nearby incidents কতগুলো?
*Example: `3`*

### Dominant Crime
সবচেয়ে বেশি কোন crime হয়েছে?
*Example: `Robbery`*

### Severity Score

**Crime Weight:**

| Crime | Weight |
|---|---|
| Murder | 100 |
| Rape | 90 |
| Kidnap | 80 |
| Robbery | 65 |
| Assault | 45 |
| BodyFound | 30 |

Nearby crime-এর average severity বের করা হয়।

### Nearest Distance
Nearest crime কত মিটার দূরে?
*Example: `47 meter`*

---

## 7. Overall Risk Engine

```
Historical + ML Prediction = Overall Risk
```

**Formula:**

```
Final Score = (Severity × 40%)
            + (Frequency × 25%)
            + (Distance × 20%)
            + (ML Prediction × 15%)
```

**Classification:**

| Score Range | Level | Recommendation |
|---|---|---|
| 0–35 | LOW | Safe to travel |
| 36–69 | MEDIUM | Proceed carefully |
| 70+ | HIGH | Choose another route |

---

## 8. Predict Point API

**Endpoint:** `POST /api/predict-point`

**Input:**

```json
{
  "latitude": 23.77,
  "longitude": 90.35,
  "weekday": "wednesday",
  "part_of_day": "morning"
}
```

**Output:**
- Historical Analysis
- ML Prediction
- Overall Analysis

---

## 9. Predict Route API

**Endpoint:** `POST /api/predict-route`

**Input:** Polyline থেকে decode করা coordinates

*Example: `A → B → C → D → E`*

প্রতিটি point-এর জন্য নিচের ধাপগুলো চলে:
- Historical Analysis
- ML Prediction
- Overall Analysis

এরপর পুরো route-এর জন্য calculate হয়:
- Average Risk
- Highest Risk
- Route Level

---

## 10. React Native + Express Integration

### Step 1
User Map-এ Source ও Destination select করল।

```
React Native → POST /navigation/safe-route → Express
```

### Step 2
Express, Google Directions API call করবে। Google ৩টা route ফেরত দিতে পারে:
- Route A
- Route B
- Route C

### Step 3 — Polyline Decode

```
Google route → Coordinates

[
  (lat, lon),
  (lat, lon),
  (lat, lon)
]
```

### Step 4
Express, Python API call করবে।

**Deployed API:** `https://safetify-ml.onrender.com`

**Request:**

```
POST /api/predict-route
```

**Body:**

```json
{
  "weekday": "wednesday",
  "part_of_day": "morning",
  "radius": 300,
  "route": [
    {
      "latitude": 23.77,
      "longitude": 90.35
    }
  ]
}
```

### Step 5
Python ফেরত দিবে:
- Route Risk Summary
- Each Point Risk
- Danger Segments

### Step 6
Express, যদি Google ৩টা route দেয়, তাহলে Python-কে ৩ বার call করবে।

| Route | Risk |
|---|---|
| Route A | 64 |
| Route B | 28 |
| Route C | 81 |

### Step 7
Express compare করবে lowest risk — *Example: `Route B`*

### Step 8
Express, React Native-এ return করবে:

```json
{
  "recommendedRoute": "Route B",
  "risk": "LOW",
  "score": 28,
  "polyline": "xxxxx",
  "dangerSegments": [...]
}
```

---

## 11. React Native UI

**Map Screen:**

| Element | Meaning |
|---|---|
| Blue Line | Google Shortest Route |
| Green Line | Safest Route |
| Red Marker | Danger Segment |
| Yellow Marker | Medium Risk |
| Green Marker | Low Risk |

**Bottom Sheet:**
- Overall Route Risk
- Recommendation
- Estimated Crime Count

---

## 12. বর্তমান Data Flow (End-to-End)

```text
User selects Source & Destination
                │
                ▼
        React Native App
                │
                ▼
      Express Backend
                │
                ▼
     Google Directions API
                │
                ▼
     Decode Polyline → Coordinates
                │
                ▼
 POST https://safetify-ml.onrender.com/api/predict-route
                │
                ▼
      FastAPI ML Service
         ├─ BallTree → Nearby incidents
         ├─ Historical risk calculation
         ├─ Random Forest → Estimated crime count
         ├─ Overall risk scoring
         └─ Route summary generation
                │
                ▼
          JSON Response
                │
                ▼
         Express compares routes
                │
                ▼
     Returns safest route to React Native
                │
                ▼
      User sees safest route + danger markers
```

---

## একটি বাস্তবিক পরামর্শ

তোমার FYP-এর জন্য এই architecture যথেষ্ট শক্তিশালী। তবে একটি limitation পরিষ্কারভাবে report-এ উল্লেখ করা উচিত:

> Model future crime নিশ্চিতভাবে predict করে না। এটি historical crime patterns + location + weekday + time-of-day ব্যবহার করে risk estimation করে এবং route comparison-এর জন্য risk score তৈরি করে। Safe route recommendation এই estimated risk score এবং historical hotspot analysis-এর সমন্বয়ের উপর ভিত্তি করে তৈরি হয়।

এভাবে claim করলে system-এর capability সঠিকভাবে উপস্থাপিত হবে এবং academic review-এর দিক থেকেও defensible থাকবে।