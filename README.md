<div align="center">

# 🛒 Retail AI Intelligence Platform

### AI-Powered Competitive Intelligence & Market Analysis for E-Commerce Retailers

[![CI/CD Status](https://github.com/Nikhilgarg0/retail-ai-intelligence/workflows/Retail%20Intelligence%20CI%2FCD/badge.svg)](https://github.com/Nikhilgarg0/retail-ai-intelligence/actions)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-blue.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

[Features](#-key-features) · [Architecture](#-system-architecture) · [Installation](#-installation) · [Usage](#-usage) · [Roadmap](#-roadmap) · [Contact](#-contact)

</div>

---

## 📖 Overview

The **Retail AI Intelligence Platform** is an end-to-end solution that automates competitive intelligence gathering, price tracking, and market analysis for retail businesses. It combines intelligent web scraping, cloud storage, and multi-agent AI systems to deliver actionable insights through a professional web dashboard powered by Flask.

### The Problem It Solves

Retail businesses constantly struggle with time-consuming manual price monitoring, lack of real-time competitive intelligence, difficulty tracking prices across multiple platforms, and limited data-driven decision making. This platform eliminates those pain points with full automation and AI-powered analysis.

---

## ✨ Key Features

### 🔍 Data Collection
- **Multi-platform scraping** — Amazon India & Flipkart
- **Smart deduplication** — Unique product ID-based tracking
- **Auto-categorization** — Electronics, Clothing, Cosmetics, Groceries, and more
- **Real-time updates** — Detect price changes as they happen

### 📊 Price Intelligence
- Historical price tracking with trend charts
- Price drop detection with configurable thresholds
- Cross-platform price comparison
- Upward/downward trend identification

### 🤖 AI-Powered Analysis

**Quick Analysis** *(~5-10 seconds)*
- Powered by Google Gemini 2.5 Flash
- Price range summaries, top-rated products, and best-value picks

**Deep Analysis** *(~5-6 minutes)*
- Multi-agent CrewAI system with 5 specialized agents:

| Agent | Role |
|-------|------|
| 🔍 Data Scout | Market trends and gap identification |
| 💰 Pricing Strategist | Pricing optimization recommendations |
| ⚠️ Risk Assessor | Market risks and competitive threats |
| 📈 Demand Forecaster | Future demand and seasonal predictions |
| 📝 Report Writer | Executive summary generation |

### 📱 Professional Dashboard
- Real-time KPIs and metrics
- Interactive product explorer with filters
- Price analytics visualizations
- Report archive with download support

### 📄 Reporting
- Professional PDF generation via ReportLab
- Downloadable analysis reports
- Historical report archive

---

## 🖼️ Screenshots

| Dashboard | Data Collection |
|-----------|----------------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Data Collection](docs/screenshots/Data-Collection.png) |

| Product Explorer | AI Insights |
|-----------------|-------------|
| ![Product Explorer](docs/screenshots/Product-Explorer.png) | ![AI Insights](docs/screenshots/AI-Insights.png) |

| Price Analytics | Reports |
|----------------|---------|
| ![Price Analytics](docs/screenshots/Price-Analytics.png) | ![Reports](docs/screenshots/Reports.png) |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              PRESENTATION TIER                          │
│       Flask REST API + HTML/CSS/JS Frontend             │
│   Dashboard · Data Collection · Product Explorer        │
│   Price Analytics · AI Insights · Reports Archive       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              BUSINESS LOGIC TIER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Scrapers   │  │  AI Agents   │  │   Reports    │  │
│  │  - Amazon    │  │  - Gemini    │  │  - PDF Gen   │  │
│  │  - Flipkart  │  │  - CrewAI    │  │  - Archive   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              DATA TIER                                  │
│           MongoDB Atlas (Cloud Database)                │
│    Products · Price History · Reports                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.11+ | Core development |
| **Web Scraping** | Selenium, BeautifulSoup4 | Data extraction |
| **Quick AI** | Google Gemini 2.5 Flash | Fast single-agent analysis |
| **Deep AI** | CrewAI + Groq (Llama 3.3) | Multi-agent deep analysis |
| **Database** | MongoDB Atlas | Cloud NoSQL storage |
| **UI Framework** | Flask + HTML/CSS/JS | Interactive dashboard |
| **PDF Generation** | ReportLab | Professional reports |
| **Data Processing** | Pandas, NumPy | Data manipulation |

### External Services
- **MongoDB Atlas** — Cloud NoSQL database (M0 Free Tier supported)
- **Google AI Studio** — Gemini API access
- **Groq Cloud** — LLM API for CrewAI agents
- **SerpAPI** — Trending product searches *(roadmap)*

---

## 🚀 Installation

### Prerequisites

- Python 3.11+
- Google Chrome (for Selenium)
- [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas/register) (free tier)
- [Gemini API Key](https://aistudio.google.com/app/apikey) (free)
- [Groq API Key](https://console.groq.com/) (free tier)

### Setup

**1. Clone the repository**
```bash
git clone https://github.com/Nikhilgarg0/retail-ai-intelligence.git
cd retail-ai-intelligence
```

**2. Create and activate a virtual environment**
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/retail_intelligence
SERPAPI_KEY=your_serpapi_key  # optional, for trending features
```

**5. Launch the dashboard**
```bash
python run_dashboard.py
```

**6. Open in browser**
```
http://localhost:5000
```

---

## 📱 Usage

### Collect Data
1. Go to **Data Collection** in the sidebar
2. Enter a product search query (e.g., `wireless headphones`)
3. Select platform — Amazon or Flipkart
4. Choose a product category
5. Click **Start Collection**

### Explore Products
1. Navigate to **Product Explorer**
2. Filter by platform, category, or view mode
3. Click any product to see its price history chart

### Run AI Analysis

**Quick Analysis:**
1. Go to **AI Insights** → select *Quick Analysis*
2. Choose a platform and click **Generate Analysis**
3. Download the PDF report

**Deep Analysis:**
1. Select *Deep Analysis (Multi-Agent)*
2. Wait ~5-6 minutes for the 5-agent collaboration to complete
3. Review each agent's individual output and the final executive summary

### Track Prices
1. Navigate to **Price Analytics**
2. Set minimum drop percentage filter
3. Identify pricing opportunities across platforms

---

## 📂 Project Structure

```
retail-ai-intelligence/
├── src/
│   ├── scrapers/
│   │   ├── base_scraper.py        # Shared scraping logic
│   │   ├── amazon_scraper.py      # Amazon India scraper
│   │   └── flipkart_scraper.py    # Flipkart scraper
│   ├── database/
│   │   └── mongo_manager.py       # MongoDB Atlas operations
│   ├── agents/
│   │   ├── analysis_agent.py      # Single-agent (Gemini)
│   │   └── crew_manager.py        # Multi-agent CrewAI system
│   ├── utils/
│   │   ├── helpers.py             # Shared utilities
│   │   └── pdf_generator.py       # PDF report generation
│   └── ui/
│       ├── index.html             # Frontend HTML
│       ├── app.js                 # Frontend JavaScript
│       └── style.css              # Frontend styles
├── config/
│   └── settings.py                # Pydantic-based configuration
├── docs/
│   ├── ARCHITECTURE.md            # System architecture docs
│   ├── LLD.md                     # Low-level design document
│   └── screenshots/               # UI screenshots
├── tests/                         # Pytest test suite
├── .github/workflows/ci-cd.yml    # CI/CD pipeline
├── run_dashboard.py               # Application entry point
├── requirements.txt
└── .env                           # Environment variables (not committed)
```

---

## 🧪 Testing

Run the full test suite:
```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

---

## 🗺️ Roadmap

**Phase 1 — Core Enhancements**
- [ ] Meesho scraper integration
- [ ] Email alerts for price drops
- [ ] Scheduled automated scraping
- [ ] Festive discount detection

**Phase 2 — Advanced Analytics**
- [ ] ML-based price prediction
- [ ] Customer review sentiment analysis
- [ ] Market share analysis
- [ ] ChromaDB vector storage for semantic report search

**Phase 3 — Scale & Deploy**
- [ ] RESTful API layer
- [ ] Multi-user support with RBAC
- [ ] Docker containerization
- [ ] Kubernetes deployment

**Phase 4 — Intelligence Layer**
- [ ] Demand forecasting models
- [ ] Anomaly detection
- [ ] Location-based logistics analysis
- [ ] Real-time streaming data pipeline

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch — `git checkout -b feature/your-feature`
3. Commit your changes — `git commit -m 'Add: your feature description'`
4. Push to the branch — `git push origin feature/your-feature`
5. Open a Pull Request

Please ensure your code passes all tests and follows the existing style conventions.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 📬 Contact

**Nikhil Garg**

[![GitHub](https://img.shields.io/badge/GitHub-Nikhilgarg0-181717?logo=github)](https://github.com/Nikhilgarg0/retail-ai-intelligence)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Nikhil--garg8982-0A66C2?logo=linkedin)](https://www.linkedin.com/in/Nikhil-garg8982)
[![Email](https://img.shields.io/badge/Email-official.nikhilgarg%40gmail.com-D14836?logo=gmail)](mailto:official.nikhilgarg@gmail.com)

---

## 🙏 Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) — Powering quick AI analysis
- [CrewAI](https://www.crewai.com/) — Multi-agent orchestration framework
- [MongoDB Atlas](https://www.mongodb.com/atlas) — Cloud database infrastructure
- [Flask](https://flask.palletsprojects.com/) — Lightweight web framework

---

<div align="center">

⭐ If you find this project useful, please consider giving it a star!

</div>