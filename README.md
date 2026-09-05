# ExpensePro AI 2.0 – Autonomous FinTech Intelligence & Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.x-black.svg)](https://palletsprojects.com/p/flask/)
[![TailwindCSS](https://img.shields.io/badge/UI-Tailwind%20CSS-38bdf8.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, multi-tenant personal finance and financial intelligence web platform. Engineered with **Flask**, **SQLAlchemy**, **Tailwind CSS**, **Chart.js**, and an in-house **NLP Machine Learning Engine**. Features real-time automatic transaction categorization, in-browser WebAssembly OCR receipt scanning, predictive spending velocity forecasting, recurring subscription tracking, and Splitwise-style group expense settlements.

---

## 🌟 Key Features

### 1. 🤖 AI & Machine Learning Services
* **Real-Time Auto-Categorization**: Lightweight Multinomial Naive Bayes classifier & TF-IDF tokenizer that predicts transaction categories (`Food`, `Transport`, `Shopping`, `Bills`, etc.) in real-time as users type transaction notes.
* **Predictive Spending Velocity & Time-Series Forecast**: Calculates daily burn rate ($\text{spend} / \text{day}$) and projects month-end expenditures with early budget exhaustion warnings.
* **Statistical Anomaly Detection**: Flags unusual transactions exceeding 2.2x the category baseline mean or standard deviation.
* **AI Financial Advisor**: Natural language monthly insights examining weekend vs. weekday spending skews, discretionary ratios, and dynamic Financial Health Scores (A+ to D).

### 2. 📷 Smart Ingestion Pipelines
* **In-Browser WebAssembly OCR (Tesseract.js)**: Optical Character Recognition running directly on client devices with **zero external OS binary dependencies**. Automatically extracts Merchant Name, Date, and Amount.
* **Editable OCR Confirmation**: Interactive preview form allowing users to review and adjust extracted values before saving.
* **Bank Statement CSV Auto-Parser**: Supports bulk ingestion from HDFC, SBI, ICICI, Axis Bank statements with automated transaction classification.

### 3. 📅 Historical Analytics & Month/Period Switcher
* **Interactive Period Switcher (`[ ◀ August 2026 ▶ ]`)**: Navigate seamlessly through any historical month or view lifetime records.
* **6-Month Month-on-Month Comparison Bar Chart**: Visual comparison of monthly expenditures across the past 6 months.

### 4. 💳 FinTech Core Modules
* **Dynamic Database Budgets**: User-customizable monthly category limits with real-time visual progress bars (Safe, Warning, Over-Budget).
* **Recurring Subscriptions Tracker**: Active renewal countdown badges (e.g., *"Renews in 3 days"*) for Netflix, Spotify, Gym, and cloud services.
* **Splitwise Group Split Engine**: Create shared expense groups (roommates, trips), record shared bills, and calculate net settlement ledgers.
* **Automated Financial Statements**: 1-Click download of publication-quality PDF Statements (ReportLab) and multi-tab Excel workbooks (Pandas / OpenPyXL).

### 5. 🎨 Modern Design & Mobile-First UX
* **Light & Dark Mode Switch**: Instant theme toggle with zero-flicker `localStorage` persistence and automatic Chart.js palette synchronization.
* **Mobile Bottom Navigation Bar**: Revolut-style sticky bottom bar on mobile screens with quick actions.
* **Multi-Tenant Security**: Session management with Flask-Login and cryptographic password hashing via `werkzeug.security`.
* **1-Click Demo Login**: Pre-seeded recruiter demo mode for instant evaluation.

---

## 🛠️ Tech Stack

* **Backend**: Python 3, Flask, Flask-SQLAlchemy (ORM), Flask-Login, Werkzeug
* **Data & ML**: NumPy, Pandas, Scikit-Learn (TF-IDF & Naive Bayes)
* **Frontend**: HTML5, Tailwind CSS, Chart.js, Tesseract.js (WASM OCR)
* **Reporting**: ReportLab (PDF Engine), OpenPyXL (Excel Engine)
* **Deployment**: Vercel Serverless / Gunicorn / Render

---

## 🚀 Quick Start (Local Setup)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ExpensePro.git
   cd ExpensePro/expense_tracker
   ```

2. **Create a virtual environment & install dependencies**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python app.py
   ```

4. **Access in Browser**:
   Navigate to `http://127.0.0.1:5000`. Click **"1-Click Demo Account"** for instant pre-populated portfolio access!

---

## ⚡ Deployment to Vercel

1. Push your code to a GitHub repository.
2. Go to [Vercel Dashboard](https://vercel.com/new).
3. Import your GitHub repository.
4. If asked for the Root Directory, leave it as `./` (root contains `vercel.json`).
5. Click **Deploy**. Vercel will automatically configure Python Serverless Functions and deploy your app!

---

## 📄 License
This project is licensed under the MIT License.
