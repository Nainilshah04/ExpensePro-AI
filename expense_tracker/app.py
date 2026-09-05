import os
import sys
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models import db, User, Expense, Budget, Subscription, Group, GroupMember, GroupExpense
from services.ai_service import ai_engine
from services.ocr_service import ocr_parser
from services.csv_service import csv_parser
from services.export_service import export_service

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "expensepro-fintech-jwt-secret-key-2026")

if os.environ.get("VERCEL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/expenses.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/favicon.ico")
def favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="24" fill="#2563EB"/><path d="M30 65 L45 45 L58 55 L72 32" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" fill="none"/><circle cx="72" cy="32" r="5" fill="#38BDF8"/></svg>"""
    return Response(svg, mimetype="image/svg+xml")

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access your financial dashboard."
login_manager.login_message_category = "info"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

DEFAULT_BUDGETS = {
    "Food": 6000.0,
    "Transport": 3000.0,
    "Shopping": 5000.0,
    "Bills": 4500.0,
    "Entertainment": 2500.0,
    "Health": 2000.0,
    "Education": 1500.0,
    "Other": 1000.0
}

def seed_demo_user():
    """Initializes a demo user with rich mock financial transactions for portfolio showcases."""
    demo_user = User.query.filter_by(username="demo").first()
    if not demo_user:
        demo_user = User(
            username="demo",
            email="demo@expensepro.ai"
        )
        demo_user.set_password("demo123")
        db.session.add(demo_user)
        db.session.commit()

        # Seed Default Budgets
        for cat, limit in DEFAULT_BUDGETS.items():
            b = Budget(user_id=demo_user.id, category=cat, monthly_limit=limit)
            db.session.add(b)

        # Seed sample transactions across current month
        today = date.today()
        sample_txs = [
            (today - timedelta(days=1), 450.0, "Food", "Swiggy gourmet burger meal", "UPI"),
            (today - timedelta(days=2), 180.0, "Transport", "Uber auto ride to campus", "UPI"),
            (today - timedelta(days=3), 1250.0, "Shopping", "Zara slim fit casual shirt", "Card"),
            (today - timedelta(days=5), 899.0, "Bills", "Airtel broadband recharge", "NetBanking"),
            (today - timedelta(days=6), 650.0, "Entertainment", "PVR Cinemas movie tickets", "UPI"),
            (today - timedelta(days=7), 420.0, "Health", "Apollo pharmacy vitamins & multivitamins", "Cash"),
            (today - timedelta(days=9), 2300.0, "Food", "Barbeque Nation team lunch", "Card"),
            (today - timedelta(days=11), 350.0, "Transport", "Metro smart card auto reload", "UPI"),
            (today - timedelta(days=13), 2999.0, "Shopping", "Amazon electronics noise-canceling headphones", "Card"),
            (today - timedelta(days=15), 1850.0, "Bills", "Electricity bill payment", "UPI"),
            (today - timedelta(days=18), 320.0, "Food", "Starbucks cold brew latte", "UPI"),
            (today - timedelta(days=20), 4500.0, "Education", "Coursera Deep Learning specialization", "Card"),
        ]
        for tx_date, amt, cat, note, pmethod in sample_txs:
            exp = Expense(user_id=demo_user.id, date=tx_date, amount=amt, category=cat, note=note, payment_method=pmethod)
            db.session.add(exp)

        # Seed Subscriptions
        demo_subs = [
            ("Netflix Premium 4K", 649.0, "Monthly", today + timedelta(days=4), "Entertainment"),
            ("Spotify Individual Music", 119.0, "Monthly", today + timedelta(days=12), "Entertainment"),
            ("Cult.fit Gym & Fitness", 1499.0, "Monthly", today + timedelta(days=18), "Health"),
            ("Amazon Prime Annual", 1499.0, "Yearly", today + timedelta(days=45), "Entertainment"),
        ]
        for name, amt, cycle, rdate, cat in demo_subs:
            sub = Subscription(user_id=demo_user.id, name=name, amount=amt, billing_cycle=cycle, next_renewal_date=rdate, category=cat)
            db.session.add(sub)

        # Seed Group Split
        grp = Group(name="Flat 402 - Expenses", description="Apartment rent, cook, and groceries", created_by=demo_user.id)
        db.session.add(grp)
        db.session.commit()

        m1 = GroupMember(group_id=grp.id, name="Demo (You)")
        m2 = GroupMember(group_id=grp.id, name="Rahul Sharma")
        m3 = GroupMember(group_id=grp.id, name="Aman Verma")
        db.session.add_all([m1, m2, m3])

        ge1 = GroupExpense(group_id=grp.id, paid_by="Demo (You)", amount=1800.0, description="Weekend grocery & fruits from D-Mart", date=today - timedelta(days=3))
        ge2 = GroupExpense(group_id=grp.id, paid_by="Rahul Sharma", amount=1200.0, description="High-speed Wi-Fi bill", date=today - timedelta(days=8))
        db.session.add_all([ge1, ge2])

        db.session.commit()

with app.app_context():
    db.create_all()
    seed_demo_user()

# --- AUTHENTICATION ROUTES ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username_or_email = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("home"))
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template("login.html")

@app.route("/demo-login", methods=["POST", "GET"])
def demo_login():
    """Allows 1-click login as Demo User for instant recruiter presentations."""
    user = User.query.filter_by(username="demo").first()
    if not user:
        seed_demo_user()
        user = User.query.filter_by(username="demo").first()
    login_user(user, remember=True)
    flash("Logged in successfully as Demo User (Portfolio Mode)!", "success")
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken. Please choose another.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html")

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Seed default budgets for new user
        for cat, limit in DEFAULT_BUDGETS.items():
            b = Budget(user_id=new_user.id, category=cat, monthly_limit=limit)
            db.session.add(b)
        db.session.commit()

        login_user(new_user)
        flash("Account created successfully! Welcome to ExpensePro.", "success")
        return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out securely.", "info")
    return redirect(url_for("login"))


# --- MAIN DASHBOARD & EXPENSE ROUTES ---

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    # 1. Filters
    start_date_str = request.form.get('start_date') or request.args.get('start_date')
    end_date_str = request.form.get('end_date') or request.args.get('end_date')
    selected_cat = request.form.get('category_filter') or request.args.get('category_filter')
    search_q = request.form.get('search') or request.args.get('search')

    # 2. Query user's expenses
    query = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc(), Expense.id.desc())

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= start_date)
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(Expense.date <= end_date)
        except ValueError:
            pass
    if selected_cat and selected_cat != "All":
        query = query.filter(Expense.category == selected_cat)
    if search_q:
        query = query.filter(Expense.note.ilike(f"%{search_q}%"))

    expenses = query.all()
    all_user_expenses = Expense.query.filter_by(user_id=current_user.id).all()

    # 3. Load Dynamic Budgets
    user_budgets = Budget.query.filter_by(user_id=current_user.id).all()
    if not user_budgets:
        for cat, limit in DEFAULT_BUDGETS.items():
            b = Budget(user_id=current_user.id, category=cat, monthly_limit=limit)
            db.session.add(b)
        db.session.commit()
        user_budgets = Budget.query.filter_by(user_id=current_user.id).all()

    # --- PERIOD SELECTION & HISTORICAL MONTH ANALYSIS ---
    today = date.today()
    current_period = f"{today.year}-{today.month:02d}"
    selected_period = request.args.get('period') or request.form.get('period') or current_period

    # Extract all distinct months present in user's expense history
    distinct_months = set()
    distinct_months.add((today.year, today.month))
    for e in all_user_expenses:
        distinct_months.add((e.date.year, e.date.month))
    sorted_months = sorted(list(distinct_months), reverse=True)
    available_periods = [
        {
            "value": f"{y}-{m:02d}",
            "label": date(y, m, 1).strftime("%B %Y"),
            "year": y,
            "month": m
        }
        for y, m in sorted_months
    ]

    # Filter data based on selected period
    if selected_period == "all":
        period_expenses = all_user_expenses
        period_label = "All Time"
        prev_period = None
        next_period = None
        is_current_month = False
    else:
        try:
            parts = selected_period.split("-")
            sel_year = int(parts[0])
            sel_month = int(parts[1])
            period_date = date(sel_year, sel_month, 1)
            period_label = period_date.strftime("%B %Y")
            period_expenses = [e for e in all_user_expenses if e.date.year == sel_year and e.date.month == sel_month]
            is_current_month = (sel_year == today.year and sel_month == today.month)

            # Prev and Next month navigation
            prev_m = 12 if sel_month == 1 else sel_month - 1
            prev_y = sel_year - 1 if sel_month == 1 else sel_year
            prev_period = f"{prev_y}-{prev_m:02d}"

            next_m = 1 if sel_month == 12 else sel_month + 1
            next_y = sel_year + 1 if sel_month == 12 else sel_year
            next_period = f"{next_y}-{next_m:02d}"
        except Exception:
            selected_period = current_period
            period_expenses = [e for e in all_user_expenses if e.date.year == today.year and e.date.month == today.month]
            period_label = today.strftime("%B %Y")
            prev_period = None
            next_period = None
            is_current_month = True

    # If no explicit start/end dates were provided in the filter, 
    # scope the recent transaction list to the selected period
    if not start_date_str and not end_date_str and selected_period != "all":
        expenses = [e for e in expenses if e.date.year == sel_year and e.date.month == sel_month]

    # Calculate category spending for the active period
    totals_by_category = {}
    for e in period_expenses:
        totals_by_category[e.category] = totals_by_category.get(e.category, 0.0) + e.amount

    period_total_spent = sum(e.amount for e in period_expenses)
    total_spent = sum(e.amount for e in expenses)

    # Calculate Budgets vs Actual for the active period
    budget_data = []
    for b in user_budgets:
        cat = b.category
        limit = b.monthly_limit
        spent = totals_by_category.get(cat, 0.0)
        percentage = round(min((spent / limit) * 100, 100) if limit > 0 else 100, 1)

        if spent > limit:
            bar_color = "bg-rose-500"
            text_color = "text-rose-600 dark:text-rose-400"
            badge = "Over Budget"
        elif percentage > 75:
            bar_color = "bg-amber-400"
            text_color = "text-amber-600 dark:text-amber-400"
            badge = "Near Limit"
        else:
            bar_color = "bg-emerald-500"
            text_color = "text-emerald-600 dark:text-emerald-400"
            badge = "On Track"

        budget_data.append({
            "id": b.id,
            "name": cat,
            "spent": spent,
            "limit": limit,
            "percent": percentage,
            "bar_color": bar_color,
            "text_color": text_color,
            "badge": badge
        })

    budget_data.sort(key=lambda x: x['spent'], reverse=True)

    # 4. AI Engine: Predictive Forecasting & Anomaly Detection
    forecast = ai_engine.calculate_spending_forecast(period_expenses if is_current_month else all_user_expenses, user_budgets)
    advisor_insights = ai_engine.generate_financial_advisor_insights(period_expenses if period_expenses else all_user_expenses, user_budgets)

    # 5. Active Subscriptions & Countdown
    subs = Subscription.query.filter_by(user_id=current_user.id, is_active=True).order_by(Subscription.next_renewal_date.asc()).all()
    sub_data = []
    total_monthly_recurring = 0.0
    for s in subs:
        days_until = (s.next_renewal_date - today).days
        total_monthly_recurring += s.amount if s.billing_cycle == "Monthly" else (s.amount / 12)
        sub_data.append({
            "id": s.id,
            "name": s.name,
            "amount": s.amount,
            "billing_cycle": s.billing_cycle,
            "renewal_date": s.next_renewal_date.strftime("%d %b %Y"),
            "days_until": days_until,
            "category": s.category,
            "is_urgent": 0 <= days_until <= 3
        })

    # 6. Group Split Summaries
    groups = Group.query.filter_by(created_by=current_user.id).all()
    groups_data = []
    for g in groups:
        g_expenses = g.expenses
        g_members = [m.name for m in g.members]
        g_total = sum(ge.amount for ge in g_expenses)
        num_members = max(1, len(g_members))
        per_person_share = g_total / num_members

        user_display = f"{current_user.username} (You)"
        user_paid = sum(ge.amount for ge in g_expenses if ge.paid_by in (user_display, "Demo (You)", current_user.username))
        net_balance = round(user_paid - per_person_share, 2)

        groups_data.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "members": g_members,
            "total_spent": g_total,
            "per_person": round(per_person_share, 2),
            "user_paid": round(user_paid, 2),
            "net_balance": net_balance,
            "expenses": [{
                "id": ge.id,
                "paid_by": ge.paid_by,
                "amount": ge.amount,
                "description": ge.description,
                "date": ge.date.strftime("%d %b")
            } for ge in g_expenses]
        })

    # 7. Charts Data: Donut Split & 6-Month Month-on-Month Comparison
    chart_labels = list(totals_by_category.keys()) if totals_by_category else ["No Expenses"]
    chart_values = list(totals_by_category.values()) if totals_by_category else [0]

    # 6-Month Month-on-Month Comparison Bar Chart
    mom_labels = []
    mom_values = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        m_expenses = [e for e in all_user_expenses if e.date.year == y and e.date.month == m]
        m_total = sum(e.amount for e in m_expenses)
        mom_labels.append(date(y, m, 1).strftime("%b %y"))
        mom_values.append(round(m_total, 2))

    categories_list = list(DEFAULT_BUDGETS.keys())

    return render_template(
        "home.html",
        expenses=expenses,
        total_spent=total_spent,
        period_total_spent=period_total_spent,
        selected_period=selected_period,
        period_label=period_label,
        available_periods=available_periods,
        prev_period=prev_period,
        next_period=next_period,
        is_current_month=is_current_month,
        budget_data=budget_data,
        forecast=forecast,
        advisor_insights=advisor_insights,
        subscriptions=sub_data,
        total_recurring=round(total_monthly_recurring, 2),
        groups=groups_data,
        chart_labels=chart_labels,
        chart_values=chart_values,
        mom_labels=mom_labels,
        mom_values=mom_values,
        categories=categories_list,
        start_date=start_date_str or "",
        end_date=end_date_str or "",
        selected_category=selected_cat or "All",
        search_query=search_q or ""
    )

@app.route("/add", methods=["POST"])
@login_required
def add_expense():
    date_str = request.form.get("date")
    amount = float(request.form.get("amount", 0))
    category = request.form.get("category", "Other")
    note = request.form.get("note", "").strip()
    payment_method = request.form.get("payment_method", "UPI")

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        date_obj = date.today()

    new_expense = Expense(
        user_id=current_user.id,
        date=date_obj,
        amount=amount,
        category=category,
        note=note,
        payment_method=payment_method
    )
    db.session.add(new_expense)
    db.session.commit()
    flash(f"Added expense ₹{amount:,.2f} under {category}.", "success")
    return redirect(url_for("home"))

@app.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash("Transaction removed successfully.", "info")
    return redirect(url_for("home"))

@app.route("/edit/<int:expense_id>", methods=["POST"])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    date_str = request.form.get("date")
    amount = float(request.form.get("amount", expense.amount))
    category = request.form.get("category", expense.category)
    note = request.form.get("note", expense.note).strip()
    payment_method = request.form.get("payment_method", expense.payment_method)

    if date_str:
        try:
            expense.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    expense.amount = amount
    expense.category = category
    expense.note = note
    expense.payment_method = payment_method

    db.session.commit()
    flash(f"Transaction updated: ₹{amount:,.2f} under {category}.", "success")
    return redirect(url_for("home"))

@app.route("/reset-demo", methods=["POST"])
@login_required
def reset_demo():
    """Allows user to re-populate standard demo transactions anytime."""
    today = date.today()
    sample_txs = [
        (today - timedelta(days=1), 450.0, "Food", "Swiggy gourmet burger meal", "UPI"),
        (today - timedelta(days=2), 180.0, "Transport", "Uber auto ride to campus", "UPI"),
        (today - timedelta(days=3), 1250.0, "Shopping", "Zara slim fit casual shirt", "Card"),
        (today - timedelta(days=5), 899.0, "Bills", "Airtel broadband recharge", "NetBanking"),
        (today - timedelta(days=6), 650.0, "Entertainment", "PVR Cinemas movie tickets", "UPI"),
        (today - timedelta(days=7), 420.0, "Health", "Apollo pharmacy vitamins & multivitamins", "Cash"),
        (today - timedelta(days=9), 2300.0, "Food", "Barbeque Nation team lunch", "Card"),
        (today - timedelta(days=11), 350.0, "Transport", "Metro smart card auto reload", "UPI"),
        (today - timedelta(days=13), 2999.0, "Shopping", "Amazon electronics noise-canceling headphones", "Card"),
        (today - timedelta(days=15), 1850.0, "Bills", "Electricity bill payment", "UPI"),
        (today - timedelta(days=18), 320.0, "Food", "Starbucks cold brew latte", "UPI"),
        (today - timedelta(days=20), 4500.0, "Education", "Coursera Deep Learning specialization", "Card"),
    ]
    for tx_date, amt, cat, note, pmethod in sample_txs:
        exp = Expense(user_id=current_user.id, date=tx_date, amount=amt, category=cat, note=note, payment_method=pmethod)
        db.session.add(exp)
    db.session.commit()
    flash("Demo transactions successfully restored!", "success")
    return redirect(url_for("home"))

@app.route("/budgets/update", methods=["POST"])
@login_required
def update_budgets():
    for key, value in request.form.items():
        if key.startswith("budget_"):
            try:
                budget_id = int(key.split("_")[1])
                new_limit = float(value)
                b = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
                if b and new_limit >= 0:
                    b.monthly_limit = new_limit
            except (ValueError, IndexError):
                pass
    db.session.commit()
    flash("Monthly budget limits updated successfully!", "success")
    return redirect(url_for("home"))

@app.route("/subscriptions/add", methods=["POST"])
@login_required
def add_subscription():
    name = request.form.get("name", "").strip()
    amount = float(request.form.get("amount", 0))
    cycle = request.form.get("billing_cycle", "Monthly")
    cat = request.form.get("category", "Entertainment")
    rdate_str = request.form.get("renewal_date")

    try:
        rdate = datetime.strptime(rdate_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        rdate = date.today() + timedelta(days=30)

    sub = Subscription(
        user_id=current_user.id,
        name=name,
        amount=amount,
        billing_cycle=cycle,
        next_renewal_date=rdate,
        category=cat
    )
    db.session.add(sub)
    db.session.commit()
    flash(f"Subscription '{name}' added successfully!", "success")
    return redirect(url_for("home"))

@app.route("/subscriptions/delete/<int:sub_id>", methods=["POST"])
@login_required
def delete_subscription(sub_id):
    sub = Subscription.query.filter_by(id=sub_id, user_id=current_user.id).first_or_404()
    db.session.delete(sub)
    db.session.commit()
    flash("Subscription removed.", "info")
    return redirect(url_for("home"))

@app.route("/groups/create", methods=["POST"])
@login_required
def create_group():
    name = request.form.get("name", "").strip()
    desc = request.form.get("description", "").strip()
    members_raw = request.form.get("members", "").strip()

    grp = Group(name=name, description=desc, created_by=current_user.id)
    db.session.add(grp)
    db.session.flush()

    # Add current user as default member
    user_member = GroupMember(group_id=grp.id, name=f"{current_user.username} (You)")
    db.session.add(user_member)

    # Add extra members
    for m in members_raw.split(","):
        cleaned_m = m.strip()
        if cleaned_m:
            db.session.add(GroupMember(group_id=grp.id, name=cleaned_m))

    db.session.commit()
    flash(f"Group '{name}' created with members!", "success")
    return redirect(url_for("home"))

@app.route("/groups/<int:group_id>/add-expense", methods=["POST"])
@login_required
def add_group_expense(group_id):
    grp = Group.query.filter_by(id=group_id, created_by=current_user.id).first_or_404()
    paid_by = request.form.get("paid_by")
    amount = float(request.form.get("amount", 0))
    desc = request.form.get("description", "").strip()
    date_str = request.form.get("date")

    try:
        tx_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        tx_date = date.today()

    ge = GroupExpense(
        group_id=grp.id,
        paid_by=paid_by,
        amount=amount,
        description=desc,
        date=tx_date
    )
    db.session.add(ge)
    db.session.commit()
    flash(f"Added ₹{amount:,.2f} shared bill to '{grp.name}'.", "success")
    return redirect(url_for("home"))

@app.route("/groups/<int:group_id>/delete", methods=["POST"])
@login_required
def delete_group(group_id):
    grp = Group.query.filter_by(id=group_id, created_by=current_user.id).first_or_404()
    db.session.delete(grp)
    db.session.commit()
    flash("Group deleted.", "info")
    return redirect(url_for("home"))


# --- AI & INGESTION APIS ---

@app.route("/api/predict-category", methods=["GET"])
def api_predict_category():
    """Real-time NLP prediction API called as user types transaction note."""
    text = request.args.get("text", "")
    pred = ai_engine.predict_category(text)
    return jsonify(pred)

@app.route("/scan/receipt", methods=["POST"])
@login_required
def scan_receipt():
    """Accepts extracted text from client-side Tesseract.js scanner or direct input."""
    raw_text = request.form.get("ocr_text", "")
    parsed = ocr_parser.parse_text(raw_text)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify(parsed)

    if parsed["success"]:
        new_expense = Expense(
            user_id=current_user.id,
            date=datetime.strptime(parsed["date"], "%Y-%m-%d").date(),
            amount=parsed["amount"],
            category=parsed["category"],
            note=f"Receipt: {parsed['merchant']}",
            payment_method="Card"
        )
        db.session.add(new_expense)
        db.session.commit()
        flash(f"Receipt scanned & auto-added: ₹{parsed['amount']} ({parsed['category']}) from {parsed['merchant']}.", "success")
    else:
        flash("Could not parse receipt text. Please try again.", "danger")

    return redirect(url_for("home"))

@app.route("/import/csv", methods=["POST"])
@login_required
def import_csv():
    """Bank statement CSV importer with bulk auto-categorization."""
    if 'csv_file' not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for("home"))

    file = request.files['csv_file']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for("home"))

    result = csv_parser.parse_csv(file)
    if not result["success"]:
        flash(result["error"], "danger")
        return redirect(url_for("home"))

    imported_count = 0
    for rec in result["records"]:
        exp = Expense(
            user_id=current_user.id,
            date=rec["date"],
            amount=rec["amount"],
            category=rec["category"],
            note=rec["note"],
            payment_method="Bank Statement"
        )
        db.session.add(exp)
        imported_count += 1

    db.session.commit()
    flash(f"Successfully imported and categorized {imported_count} bank transactions!", "success")
    return redirect(url_for("home"))


# --- EXPORT REPORTS ---

@app.route("/export/pdf")
@login_required
def export_pdf():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    user_budgets = Budget.query.filter_by(user_id=current_user.id).all()
    total_spent = sum(e.amount for e in expenses)

    budget_data = []
    cat_totals = {}
    for e in expenses:
        cat_totals[e.category] = cat_totals.get(e.category, 0.0) + e.amount
    for b in user_budgets:
        spent = cat_totals.get(b.category, 0.0)
        pct = (spent / b.monthly_limit * 100) if b.monthly_limit > 0 else 100
        budget_data.append({"name": b.category, "spent": spent, "limit": b.monthly_limit, "percent": pct})

    pdf_buffer = export_service.generate_pdf(expenses, current_user, total_spent, budget_data)
    filename = f"ExpensePro_Statement_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")

@app.route("/export/excel")
@login_required
def export_excel():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    excel_buffer = export_service.generate_excel(expenses, current_user)
    filename = f"ExpensePro_Report_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return send_file(excel_buffer, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    app.run(debug=True, port=5000)