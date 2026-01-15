# SheSafe

**SheSafe** is a mobile-first Progressive Web App (PWA) designed to provide **safe, clean, and verified sanitation access for women**, using **existing infrastructure** such as restaurants, dhabas, fuel stations, and public venues.

The project aligns with **UN SDG 11 – Sustainable Cities & Communities**, focusing on safety, accessibility, and inclusive urban (and semi-urban) infrastructure.

This repository represents an **MVP built incrementally**, with a strong emphasis on transparency, safety, and real-world usability.

---

## Problem Statement

Women travelers—especially in India—face significant challenges in accessing:
- Clean public washrooms
- Safe washrooms at night
- Predictable sanitation facilities during long journeys

Existing public facilities are:
- Poorly maintained
- Unsafe after dark
- Unverified
- Hard to locate reliably

This leads to:
- Health issues (e.g., UTIs)
- Safety risks
- Travel anxiety
- Reduced mobility freedom for women

---

## Solution Overview

SheSafe creates a **verified sanitation network** by onboarding existing businesses and making their washrooms:
- Discoverable
- Bookable
- Rated
- Traceable

Key principles:
- Asset-light (no construction)
- Women-first design
- Transparency over guarantees
- Safety through accountability

---

## Core Features (MVP)

### For Users (Women Only)
- Simple signup & login
- GPS-based discovery of nearby washrooms
- Ranked listings based on safety & hygiene
- Booking confirmation
- Pay via app or at location
- Multi-parameter feedback & ratings

### For Vendors
- Self-registration & onboarding
- Location pinning (GPS coordinates)
- Safety attribute declaration
- Image uploads
- Availability configuration
- Earnings & usage dashboard

### For Admin
- Vendor approval & moderation
- System-wide analytics
- Revenue tracking
- Feedback oversight

---

## Tech Stack (Locked for MVP)

### Backend
- Python 3.x
- Flask
- Flask-Login
- SQLAlchemy
- SQLite
- Flask-Migrate (optional but recommended)

### Frontend
- HTML + CSS (mobile-first)
- Vue.js (lightweight usage)
- Leaflet.js (maps)
- OpenStreetMap (map tiles)

### Platform
- Progressive Web App (PWA)
- No native Android/iOS apps
- No paid APIs
- No Google Maps

---

## Project Architecture

/shesafe
│
├── app/
│ ├── init.py
│ ├── models.py
│ ├── routes/
│ ├── templates/
│ ├── static/
│ └── utils/
│
├── migrations/
├── config.py
├── run.py
├── manifest.json
├── service-worker.js
└── README.md


---

## User Roles

### 1. Admin
- Full access to all data
- Approves or rejects vendors
- Enables or disables vendors
- Views system analytics and revenue

### 2. Vendor
- Registers business property
- Submits washroom details
- Uploads images
- Sets availability & safety parameters
- Views bookings and earnings

### 3. User (Women)
- Discovers nearby washrooms
- Books access
- Submits feedback and ratings

---

## Database Models (Conceptual)

### User
- id
- name
- email
- password_hash
- role (admin / vendor / user)
- created_at

---

### Vendor
- id
- user_id (FK → User)
- business_name
- description
- latitude
- longitude
- address
- has_cctv (boolean)
- has_female_staff (boolean)
- female_staff_start_time (nullable)
- female_staff_end_time (nullable)
- is_verified (boolean)
- is_active (boolean)
- average_rating (float)
- created_at

---

### VendorImage
- id
- vendor_id (FK → Vendor)
- image_url
- uploaded_at

---

### Booking
- id
- user_id (FK → User)
- vendor_id (FK → Vendor)
- booking_time
- visit_date
- payment_mode (app / pay_at_location)
- amount
- status

---

### Feedback
- id
- booking_id (FK → Booking)
- user_id (FK → User)
- vendor_id (FK → Vendor)
- hygiene_rating (1–5)
- safety_rating (1–5)
- staff_behavior_rating (1–5)
- overall_rating (1–5)
- comments
- created_at

---

## Safety & Transparency Design

- **No absolute safety claims**
- Safety is improved through:
  - Vendor verification
  - Booking traceability
  - Visible safety indicators
  - Time-based staff availability
- Female staff availability and CCTV presence are:
  - Transparent
  - Used as ranking signals
  - Not mandatory for listing

---

## Ranking Logic (High-Level)

Vendors are ranked based on:
- Distance from user
- Average rating
- Female staff availability at current time
- CCTV availability

Visual cues:
- Green: Female staff available
- Orange: Female staff not available
- Icons for CCTV presence

---

## Maps & Location

- Browser Geolocation API
- Leaflet.js for rendering
- OpenStreetMap tiles
- Vendor coordinates stored in DB
- Simple distance-based filtering

---

## Progressive Web App (PWA)

SheSafe is designed as a PWA:
- Installable on mobile devices
- Fullscreen standalone mode
- Low-bandwidth friendly
- Mobile-first UX

---

## Development Philosophy

- Built incrementally with clear commits
- MVP-first, not feature-heavy
- Realistic constraints
- Hackathon-friendly
- Scalable architecture

---

## Non-Goals (MVP)

- No native mobile apps
- No OTP or Aadhaar authentication
- No real-time tracking
- No advanced navigation
- No machine learning

---

## Status

🚧 **Active MVP Development**  
This README acts as the **single source of truth** for project intent and scope.

All contributors and AI tools should follow the constraints and architecture defined here.
