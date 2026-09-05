# Skills and Concepts Learned: ExpensePro AI 2.0 (FinTech Platform)

## 1. Advanced Python Web Architecture & Multi-Tenancy
- **Modular Flask Development**: Separation of concerns across database models (`models.py`), AI/ML services (`services/ai_service.py`), OCR extraction (`services/ocr_service.py`), CSV parsing (`services/csv_service.py`), and PDF/Excel generation (`services/export_service.py`).
- **Authentication & Security**: Implemented Flask-Login session management with password hashing via `werkzeug.security` (PBKDF2/SHA256). Every database record is strictly scoped to `current_user.id` to prevent unauthorized cross-tenant access.
- **Relational Database Modeling (SQLAlchemy ORM)**: Designed relational schemas with foreign key constraints, one-to-many relationships, cascade deletion, and automated migration seeding.

## 2. Artificial Intelligence & Machine Learning
- **Natural Language Processing (NLP)**: Implemented text tokenization and a Multinomial Naive Bayes classifier with Laplace smoothing to predict transaction categories in real-time as users type.
- **Predictive Spending Velocity & Time-Series Forecasting**: Modeled cumulative daily burn rate to estimate month-end spending trajectories and predict exact calendar days when category budgets will be exhausted.
- **Anomaly Detection**: Applied statistical variance and standard deviation thresholds to detect unusual single-transaction spending spikes (>2.2x category mean).
- **Rule-Augmented Heuristics**: Combined probabilistic ML models with deterministic pattern matching for merchant identification.

## 3. Computer Vision & Ingestion Pipelines
- **Client-Side WebAssembly OCR (Tesseract.js)**: Embedded in-browser optical recognition to read receipts without requiring heavy external C++ binaries on the host OS.
- **Entity Extraction**: Applied regex engines to identify merchant names, ISO and localized date formats, and total transaction amounts from unstructured receipt text.
- **Bank Statement CSV Ingestion**: Built a Pandas-based parser that handles varied bank statement schemas (HDFC, SBI, ICICI), normalizes debit amounts, and auto-tags entries.

## 4. FinTech Specific Business Logic
- **Dynamic Category Budgeting**: Real-time percentage tracking, color-coded visual thresholds (Safe, Warning, Danger), and user-customizable monthly limits.
- **Recurring Subscriptions Management**: Countdown algorithms tracking days until renewal for services like Netflix, Spotify, and Gym, calculating monthly recurring commitments.
- **Splitwise Group Settlement Algorithm**: Calculated net balances, total expenditure, per-person equal splits, and debtor-creditor settlement balances.

## 5. Automated Financial Reporting
- **ReportLab PDF Generation**: Programmatic generation of branded, publication-quality financial statements with KPI summaries, budget tables, and transaction histories.
- **Multi-Tab Excel Workbooks**: Export of structured raw transactions and grouped category pivot tables via Pandas and OpenPyXL.

## 6. High-End UI/UX Engineering
- **Modern FinTech Design**: Glassmorphism cards, modern slate/indigo dark mode, glowing accents, and responsive layout built with Tailwind CSS.
- **Dynamic Visual Analytics**: Interactive Doughnut and Line charts integrated using Chart.js.
- **Asynchronous User Experience**: Live debounced AJAX API calls (`/api/predict-category`) providing immediate feedback without page reloads.