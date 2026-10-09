<div align="center">

# DECORREACH

### Find the shops that will stock your home decor.

<p>
  <strong>API-driven B2B buyer discovery & outreach platform for US home-decor sellers.</strong>
</p>

<p>
  Discover businesses · Find public contacts · Review buyers · Personalize outreach · Send
</p>

<br>

<a href="https://homedecor-seller.onrender.com/">
  <img src="https://img.shields.io/badge/Live%20Demo-Visit%20DecorReach-C9A227?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Live Demo">
</a>
<a href="https://github.com/jasminefloraa/HomeDecor_seller">
  <img src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
</a>

<br><br>

<img src="https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Flask-Backend-000000?style=flat-square&logo=flask&logoColor=white">
<img src="https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?style=flat-square&logo=javascript&logoColor=black">
<img src="https://img.shields.io/badge/Google%20Places-API-4285F4?style=flat-square&logo=googlemaps&logoColor=white">
<img src="https://img.shields.io/badge/SMTP-Email-EA4335?style=flat-square&logo=gmail&logoColor=white">
<img src="https://img.shields.io/badge/Render-Deployed-46E3B7?style=flat-square&logo=render&logoColor=black">

</div>

---

## Overview

**DecorReach** is a full-stack B2B prospecting application built for home-decor sellers who need to identify potential retail stores and interior-design businesses across the United States.

The platform combines **live business discovery, public contact discovery, buyer review, personalized email outreach, and campaign tracking** into a single workflow.

Instead of manually searching multiple websites and maintaining spreadsheets, sellers can use DecorReach to build a targeted buyer list and start outreach from one interface.

### The idea

> **Don't just find businesses. Find the businesses that could actually stock your products.**

---

## Live Product

### Try DecorReach

**Live Application**

https://homedecor-seller-1.onrender.com/

**Source Code**

https://github.com/jasminefloraa/HomeDecor_seller

---

# Product Workflow

```text
┌──────────────────────┐
│   Define Target      │
│   City + State       │
│   + Shop Type        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Business Discovery  │
│   Google Places API  │
│   OpenStreetMap      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Business Profile   │
│                      │
│ Name • Website       │
│ Address • Phone      │
│ Rating • Category    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Contact Discovery  │
│                      │
│ Website              │
│ Contact Pages        │
│ OSM                   │
│ Hunter API            │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     Buyer Review     │
│                      │
│ Select relevant      │
│ businesses           │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Personalized Email   │
│                      │
│ Subject + Message    │
│ Business Context     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    SMTP Delivery     │
│                      │
│ Success / Failure    │
│ Tracking             │
└──────────────────────┘
```

---

# Why DecorReach?

Traditional B2B prospecting can involve several disconnected tools:

```text
Google Search
     ↓
Business Website
     ↓
Contact Page
     ↓
Spreadsheet
     ↓
Email Client
     ↓
Manual Tracking
```

DecorReach brings the core workflow together:

```text
              DECORREACH

Search → Discover → Enrich → Review → Personalize → Send → Track
```

This makes the process more structured, repeatable, and scalable.

---

# Features

<table>
<tr>
<td width="50%">

### Business Discovery

Search for relevant US businesses using:

* City
* State
* Shop category
* Retail businesses
* Interior designers

</td>

<td width="50%">

### Live Business Data

Retrieve available business information such as:

* Name
* Category
* Address
* Phone
* Website
* Rating

</td>
</tr>

<tr>
<td>

### Contact Discovery

Find publicly available business emails through:

* Business websites
* Contact pages
* Public website data
* OpenStreetMap
* Hunter API

</td>

<td>

### Buyer Qualification

Review discovered businesses before outreach and focus on businesses relevant to the seller's products.

</td>
</tr>

<tr>
<td>

### Personalized Outreach

Prepare business-specific B2B emails with:

* Recipient
* Subject
* Personalized content
* Sender identity
* Reply-to address

</td>

<td>

### Email Delivery

Send directly through an authenticated SMTP mailbox and record:

* Successful deliveries
* Failed attempts
* Recipient
* Business
* Error information

</td>
</tr>
</table>

---

# Tech Stack

## Backend

<p>
<img src="https://skillicons.dev/icons?i=python,flask" height="48">
</p>

* **Python**
* **Flask**
* REST-style API endpoints
* SMTP email delivery
* JSON-based local persistence
* Environment-based configuration

---

## Frontend

<p>
<img src="https://skillicons.dev/icons?i=html,css,js" height="48">
</p>

* HTML5
* CSS3
* Vanilla JavaScript
* Responsive UI
* Interactive dashboard
* Dynamic API-driven rendering

---

## APIs & Services

| Service           | Purpose                               |
| ----------------- | ------------------------------------- |
| Google Places API | Live business discovery               |
| OpenStreetMap     | Business discovery fallback           |
| Hunter API        | Optional domain-based email discovery |
| Gmail SMTP        | Email delivery                        |
| Render            | Cloud deployment                      |

---

# Architecture

```text
                         ┌─────────────────────┐
                         │    DECORREACH       │
                         │    Web Interface    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Flask Backend    │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
       ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
       │ Google Places  │  │ OpenStreetMap  │  │  Hunter API    │
       │      API       │  │    Fallback    │  │   (Optional)   │
       └────────────────┘  └────────────────┘  └────────────────┘
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Business / Email   │
                         │       Results       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   SMTP Mail Server  │
                         │   Gmail / SMTP      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Delivery Tracking  │
                         └─────────────────────┘
```

---

# API Endpoints

DecorReach exposes a lightweight Flask API.

### Check service configuration

```http
GET /api/status
```

Returns the availability of:

* Google Places
* Hunter
* SMTP mail configuration

---

### Discover businesses

```http
POST /api/search
```

Example request:

```json
{
  "city": "Austin",
  "state": "TX",
  "types": [
    "home decor store",
    "interior designer"
  ]
}
```

Returns discovered businesses and the data source used.

---

### Find business email

```http
POST /api/email
```

The endpoint checks available public contact sources and optional Hunter enrichment.

---

### Send email

```http
POST /api/send
```

Example:

```json
{
  "to": "buyer@example.com",
  "subject": "Home decor partnership",
  "body": "Hello, I wanted to introduce our collection...",
  "business": "Example Home",
  "from_name": "Jasmine Flora"
}
```

---

### Record discovered email count

```http
POST /api/found
```

Used to update search statistics after contact discovery.

---

### Dashboard statistics

```http
GET /api/stats
```

Provides:

* Total searches
* Businesses discovered
* Emails found
* Successful sends
* Failed sends
* Recent activity
* Daily sending statistics

---

# Project Structure

```text
HomeDecor_seller/
│
├── static/
│   └── index.html
│
├── app.py
├── emailfinder.py
├── index.html
│
├── requirements.txt
├── .env.example
├── .gitignore
│
└── README.md
```

### Main components

| File               | Responsibility                                        |
| ------------------ | ----------------------------------------------------- |
| `app.py`           | Flask application, APIs, search, email sending        |
| `emailfinder.py`   | Website/public email discovery                        |
| `index.html`       | Main application interface                            |
| `static/`          | Static frontend assets                                |
| `requirements.txt` | Python dependencies                                   |
| `.env.example`     | Environment configuration template                    |
| `.gitignore`       | Prevents secrets and local files from being committed |

---

# Environment Configuration

Create a `.env` file in the project root.

```env
GOOGLE_PLACES_KEY=your_google_places_api_key

HUNTER_KEY=your_hunter_api_key

SMTP_USER=your_email@gmail.com
SMTP_PASS=your_gmail_app_password

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465

SENDER_NAME=Your Name

POSTAL_ADDRESS=Your Business Address
```

### Important

Never commit `.env` to GitHub.

The repository uses `.gitignore` to keep sensitive credentials outside source control.

```text
.env
venv/
.venv/
__pycache__/
*.pyc
data.json
```

---

# Local Development

## 1. Clone the repository

```bash
git clone https://github.com/jasminefloraa/HomeDecor_seller.git
cd HomeDecor_seller
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create:

```text
.env
```

and add the required API and SMTP credentials.

---

## 5. Start the application

### Development

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

### Production

DecorReach can run with Gunicorn:

```bash
gunicorn app:app
```

---

# Deployment

DecorReach is deployed using **Render**.

### Production URL

https://homedecor-seller-1.onrender.com/

### Render configuration

**Build Command**

```bash
pip install -r requirements.txt
```

**Start Command**

```bash
gunicorn app:app
```

### Required Render Environment Variables

```text
GOOGLE_PLACES_KEY
HUNTER_KEY
SMTP_USER
SMTP_PASS
SMTP_HOST
SMTP_PORT
SENDER_NAME
POSTAL_ADDRESS
```

Secrets are configured through Render's environment settings rather than committed to GitHub.

---

# Data Flow

### Business discovery

```text
User Input
   │
   ├── City
   ├── State
   └── Shop Type
          │
          ▼
    Google Places
          │
          ▼
   Business Results
          │
          ▼
      DecorReach UI
```

### Email discovery

```text
Business Website
       │
       ▼
Contact / About / Website Pages
       │
       ▼
Public Email Detection
       │
       ├──── Found ────► Return Email
       │
       └──── Not Found
                 │
                 ▼
            Hunter API
                 │
                 ▼
             Email Result
```

### Outreach

```text
Selected Buyer
      │
      ▼
Personalized Message
      │
      ▼
SMTP Authentication
      │
      ▼
Email Delivery
      │
      ├── Success
      │
      └── Failure
```

---

# Responsible Outreach

DecorReach is designed around **targeted B2B outreach**, not indiscriminate bulk messaging.

The application:

* Uses publicly available business information.
* Keeps the seller involved in buyer selection.
* Supports personalized communication.
* Uses authenticated email delivery.
* Records successful and failed attempts.
* Includes an unsubscribe instruction in outbound messages.

Users are responsible for complying with applicable email, privacy, data-protection, and anti-spam requirements when using the platform.

---

# Security

Sensitive credentials are intentionally kept outside the repository.

### Protected credentials

```text
Google API Key
Hunter API Key
SMTP Username
SMTP Password
```

They are loaded through environment variables:

```python
os.getenv("GOOGLE_PLACES_KEY")
os.getenv("HUNTER_KEY")
os.getenv("SMTP_USER")
os.getenv("SMTP_PASS")
```

This prevents credentials from being hard-coded into the application.

---

# Current Capabilities

```text
[✓] US business discovery
[✓] City/state targeting
[✓] Shop-type targeting
[✓] Google Places integration
[✓] OpenStreetMap fallback
[✓] Website contact discovery
[✓] Hunter API integration
[✓] Buyer review
[✓] Personalized outreach
[✓] Gmail SMTP integration
[✓] Success/failure tracking
[✓] Dashboard statistics
[✓] Environment-based secrets
[✓] Render deployment
[✓] Production Gunicorn server
```

---

# Future Improvements

The architecture can be extended with:

* PostgreSQL database
* Persistent campaign management
* Buyer tagging and segmentation
* Lead scoring
* Advanced duplicate detection
* Email templates
* Scheduled follow-ups
* Open/click tracking
* CRM integrations
* Authentication and user accounts
* Multi-user workspaces
* Persistent analytics
* Exportable buyer lists
* Additional business-data providers

---

# Engineering Highlights

This project demonstrates practical experience with:

**Backend Development**

* Flask REST APIs
* Request validation
* External API integration
* SMTP integration
* Error handling
* Environment configuration

**Frontend Development**

* Responsive UI
* Dynamic API consumption
* Interactive business cards
* Search workflows
* Dashboard statistics

**API Integration**

* Google Places
* OpenStreetMap
* Hunter
* SMTP

**Deployment**

* Git/GitHub
* Render
* Gunicorn
* Production environment variables

**Software Practices**

* Secrets excluded from source control
* Fallback data provider
* Modular email discovery
* API-driven architecture
* Delivery logging
* Error tracking

---

# Screenshots

Add screenshots of the live application here:

```text
docs/
├── hero.png
├── search-results.png
├── buyer-details.png
├── outreach.png
└── dashboard.png
```

Then display them in the README:

```markdown
![DecorReach Dashboard](docs/hero.png)

![Business Discovery](docs/search-results.png)

![Buyer Outreach](docs/outreach.png)
```

> Tip: A strong README looks much more professional once these screenshots are added.

---

# Demo Scenario

### Example target

```text
Location:
Austin, TX

Business Type:
Home Decor Store
Interior Designer
```

### DecorReach workflow

```text
Search Austin
      ↓
Discover relevant businesses
      ↓
Review business websites
      ↓
Find public contact information
      ↓
Select suitable buyers
      ↓
Create personalized outreach
      ↓
Send through connected mailbox
      ↓
Track delivery result
```

---

# What Makes DecorReach Different?

DecorReach isn't simply a business search interface.

It connects multiple stages of the B2B prospecting workflow:

```text
              ┌─────────────┐
              │   DISCOVER  │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │   ENRICH    │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │    REVIEW   │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │ PERSONALIZE │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │    SEND     │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │    TRACK    │
              └─────────────┘
```

The goal is simple:

> **Turn business discovery into actionable buyer outreach.**

---

# Author

<div align="center">

### Jasmine Flora J

**B.Tech Computer Science & Engineering**

Aspiring Software Developer

<br>

<a href="https://github.com/jasminefloraa">
  <img src="https://img.shields.io/badge/GitHub-jasminefloraa-181717?style=for-the-badge&logo=github&logoColor=white">
</a>
<a href="https://www.linkedin.com/in/jasmine-flora/">
  <img src="https://img.shields.io/badge/LinkedIn-Jasmine%20Flora-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white">
</a>

<br><br>

Built with Python, Flask, JavaScript, APIs, and a focus on solving a real B2B workflow problem.

</div>

---

<div align="center">

### DECORREACH

**Discover businesses. Find buyers. Start conversations.**

<br>

<a href="https://homedecor-seller-1.onrender.com/">
  <img src="https://img.shields.io/badge/Explore%20the%20Live%20App-C9A227?style=for-the-badge&logo=googlechrome&logoColor=white">
</a>

</div>
