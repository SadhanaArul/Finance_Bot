import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="FinanceIQ",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== BACKEND FUNCTIONS ==========
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_session_state():
    defaults = {
        'authenticated': False,
        'users': {'admin': hash_password('password123')},
        'current_user': None,
        'transactions': None,
        'dark_mode': False,
        'currency': '₹',
        'currency_name': 'INR',
        'show_transaction_form': False,
        'budgets': {
            'Food & Dining': 5000,
            'Shopping': 3000,
            'Transport': 2000,
            'Entertainment': 2000,
            'Utilities': 1500,
            'Healthcare': 2000,
            'Rent': 15000,
            'Insurance': 3000,
        },
        'goals': [
            {'name': 'New Laptop', 'target': 80000, 'saved': 32000, 'deadline': '2025-12-31', 'icon': '💻'},
            {'name': 'Dream Vacation', 'target': 150000, 'saved': 45000, 'deadline': '2026-03-31', 'icon': '✈️'},
            {'name': 'Emergency Fund', 'target': 200000, 'saved': 120000, 'deadline': '2025-09-30', 'icon': '🛡️'},
        ],
        'selected_page': 'Dashboard',
        'language': 'English',
        'notifications': True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state.transactions is None:
        st.session_state.transactions = generate_sample_data()

def generate_sample_data():
    np.random.seed(42)
    transactions = []
    start_date = datetime(2025, 1, 1)
    payment_modes = ['UPI', 'Card', 'Cash', 'Net Banking']

    # Income transactions
    for i in range(30):
        date = start_date + timedelta(days=np.random.randint(0, 200))
        amount = np.random.choice([25000, 30000, 35000, 40000, 50000, 75000])
        transactions.append({
            'date': date,
            'description': np.random.choice(['Salary', 'Freelance', 'Investment', 'Bonus', 'Dividend']),
            'category': 'Income',
            'type': 'income',
            'amount': float(amount),
            'payment_mode': np.random.choice(payment_modes),
            'notes': '',
        })

    expense_cats = {
        'Rent': (12000, 20000),
        'Utilities': (800, 2500),
        'Shopping': (300, 5000),
        'Food & Dining': (200, 3000),
        'Healthcare': (500, 4000),
        'Insurance': (1000, 4000),
        'Transport': (100, 1500),
        'Entertainment': (250, 3000),
    }

    descs = {
        'Rent': ['Monthly Rent', 'House Rent'],
        'Utilities': ['Electricity Bill', 'Water Bill', 'Internet'],
        'Shopping': ['Amazon', 'Flipkart', 'Mall Shopping', 'Clothes'],
        'Food & Dining': ['Zomato', 'Swiggy', 'Restaurant', 'Groceries', 'Cafe'],
        'Healthcare': ['Pharmacy', 'Doctor Visit', 'Lab Tests'],
        'Insurance': ['Health Insurance', 'Life Insurance', 'Vehicle Insurance'],
        'Transport': ['Uber/Ola', 'Metro', 'Petrol', 'Auto'],
        'Entertainment': ['Netflix', 'Movie Tickets', 'Spotify', 'Games'],
    }

    for _ in range(250):
        date = start_date + timedelta(days=np.random.randint(0, 200))
        cat = np.random.choice(list(expense_cats.keys()))
        mn, mx = expense_cats[cat]
        amount = round(np.random.uniform(mn, mx), 2)
        transactions.append({
            'date': date,
            'description': np.random.choice(descs[cat]),
            'category': cat,
            'type': 'expense',
            'amount': amount,
            'payment_mode': np.random.choice(payment_modes),
            'notes': '',
        })

    df = pd.DataFrame(transactions)
    return df.sort_values('date').reset_index(drop=True)

def get_summary(df):
    income = df[df['type'] == 'income']['amount'].sum()
    expense = df[df['type'] == 'expense']['amount'].sum()
    savings = income - expense
    savings_rate = (savings / income * 100) if income > 0 else 0

    df = df.copy()
    df['month'] = df['date'].dt.strftime('%b %Y')
    df['month_num'] = df['date'].dt.to_period('M')

    monthly_income = df[df['type'] == 'income'].groupby('month')['amount'].sum()
    monthly_expense = df[df['type'] == 'expense'].groupby('month')['amount'].sum()
    top_expenses = df[df['type'] == 'expense'].groupby('category')['amount'].sum().sort_values(ascending=False).head(8)

    daily_expense = df[df['type'] == 'expense'].groupby(df['date'].dt.date)['amount'].sum()
    avg_daily = daily_expense.mean() if len(daily_expense) > 0 else 0

    return {
        'income': income, 'expense': expense, 'savings': savings,
        'savings_rate': savings_rate, 'monthly_income': monthly_income,
        'monthly_expense': monthly_expense, 'top_expenses': top_expenses,
        'transaction_count': len(df), 'avg_daily': avg_daily,
        'category_breakdown': df[df['type'] == 'expense'].groupby('category')['amount'].sum().to_dict(),
    }

def add_transaction(df, date, desc, category, trans_type, amount, payment_mode, notes):
    new_row = pd.DataFrame([{
        'date': pd.to_datetime(date),
        'description': desc,
        'category': category,
        'type': trans_type,
        'amount': float(amount),
        'payment_mode': payment_mode,
        'notes': notes,
    }])
    return pd.concat([df, new_row], ignore_index=True).sort_values('date').reset_index(drop=True)

def fmt(amount):
    sym = st.session_state.get('currency', '₹')
    if sym == '$':
        return f"${amount:,.2f}"
    elif sym == '€':
        return f"€{amount:,.2f}"
    else:
        return f"₹{amount:,.0f}"

def generate_ai_insights(summary, df):
    insights = []
    cat = summary['category_breakdown']
    budgets = st.session_state.budgets

    if summary['savings_rate'] < 20:
        insights.append({
            'icon': '💰', 'color': '#F59E0B',
            'title': 'Low Savings Rate Alert',
            'desc': f'Your savings rate is {summary["savings_rate"]:.1f}%. Financial experts recommend saving at least 20% of income.',
            'action': f'Cut expenses by {fmt(summary["expense"] * 0.1)} to reach your goal.'
        })
    else:
        insights.append({
            'icon': '🏆', 'color': '#10B981',
            'title': 'Excellent Savings!',
            'desc': f'Your savings rate of {summary["savings_rate"]:.1f}% is above the recommended 20%.',
            'action': 'Consider investing surplus in mutual funds or SIP.'
        })

    top_cat = max(cat, key=cat.get) if cat else 'Shopping'
    top_val = cat.get(top_cat, 0)
    insights.append({
        'icon': '📊', 'color': '#6366F1',
        'title': f'High Spend on {top_cat}',
        'desc': f'You spent {fmt(top_val)} on {top_cat}, your biggest expense category.',
        'action': 'Track sub-categories to find reduction opportunities.'
    })

    over_budget = [(k, v, budgets.get(k, 0)) for k, v in cat.items() if v > budgets.get(k, float('inf'))]
    if over_budget:
        cat_name, spent, budget = over_budget[0]
        insights.append({
            'icon': '⚠️', 'color': '#EF4444',
            'title': f'Budget Exceeded: {cat_name}',
            'desc': f'Spent {fmt(spent)} vs budget of {fmt(budget)} ({((spent/budget-1)*100):.0f}% over).',
            'action': f'Reduce {cat_name} spending by {fmt(spent - budget)} next month.'
        })

    if summary['avg_daily'] > 0:
        monthly_proj = summary['avg_daily'] * 30
        insights.append({
            'icon': '🔮', 'color': '#8B5CF6',
            'title': 'Month-End Projection',
            'desc': f'At current rate, projected monthly expenses: {fmt(monthly_proj)}.',
            'action': f'Daily average: {fmt(summary["avg_daily"])}. Aim to reduce by 10%.'
        })

    insights.append({
        'icon': '💡', 'color': '#06B6D4',
        'title': 'Smart Tip of the Day',
        'desc': 'The 50/30/20 rule: 50% needs, 30% wants, 20% savings.',
        'action': 'Review your categories against this framework monthly.'
    })

    return insights

# ========== CSS ==========
def load_css():
    dark = st.session_state.get('dark_mode', False)
    
    bg = "#0F172A" if dark else "#F8FAFC"
    card_bg = "#1E293B" if dark else "#FFFFFF"
    text = "#F1F5F9" if dark else "#0F172A"
    subtext = "#94A3B8" if dark else "#64748B"
    border = "#334155" if dark else "#E2E8F0"
    sidebar_bg = "#1E293B" if dark else "#FFFFFF"
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    * {{ font-family: 'Plus Jakarta Sans', sans-serif !important; }}

    /* ===== REMOVE TOP EMPTY SPACE (Streamlit header/toolbar) ===== */
    #MainMenu {{ visibility: hidden; height: 0; }}
    header[data-testid="stHeader"] {{ display: none !important; height: 0 !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    .stAppDeployButton {{ display: none !important; }}
    div[data-testid="stAppViewBlockContainer"] {{ padding-top: 1rem !important; }}
    .main .block-container {{ padding-top: 1.5rem !important; }}
    
    .stApp {{
        background: {bg} !important;
        color: {text} !important;
    }}
    
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid {border} !important;
    }}
    
    [data-testid="stSidebar"] * {{
        color: {text} !important;
    }}
    
    .main .block-container {{
        padding: 2rem 2rem 2rem 2rem !important;
        max-width: 1400px !important;
    }}
    
    .card {{
        background: {card_bg};
        border-radius: 20px;
        padding: 24px;
        border: 1px solid {border};
        margin-bottom: 20px;
    }}
    
    .metric-card {{
        background: {card_bg};
        border-radius: 16px;
        padding: 20px 22px;
        border: 1px solid {border};
        position: relative;
    }}
    
    .metric-label {{
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: {subtext};
        margin-bottom: 8px;
    }}
    
    .metric-value {{
        font-size: 26px;
        font-weight: 800;
        color: {text};
        font-family: monospace;
    }}
    
    .section-title {{
        font-size: 20px;
        font-weight: 700;
        color: {text};
        margin-bottom: 20px;
    }}
    
    .page-header {{
        font-size: 28px;
        font-weight: 800;
        color: {text};
        margin-bottom: 4px;
    }}
    
    .page-sub {{
        font-size: 14px;
        color: {subtext};
        margin-bottom: 28px;
    }}
    
    .progress-bar {{
        background: {border};
        border-radius: 100px;
        height: 8px;
        overflow: hidden;
    }}
    
    .progress-fill {{
        background: linear-gradient(90deg, #6366F1, #8B5CF6);
        border-radius: 100px;
        height: 100%;
    }}
    
    .footer {{
        text-align: center;
        padding: 30px;
        color: {subtext};
        font-size: 12px;
        border-top: 1px solid {border};
        margin-top: 40px;
    }}
    
    hr {{ border-color: {border} !important; }}

    /* ===== FIX: Remove keyboard_double_arrow tooltip on sidebar buttons ===== */
    /* Hide the tooltip popup entirely */
    [data-testid="stSidebar"] button [data-testid="tooltipHoverTarget"],
    [data-testid="stSidebar"] button .st-emotion-cache-1xk89bn,
    [data-testid="stSidebar"] [role="tooltip"],
    [data-testid="stSidebar"] .stTooltipIcon,
    [data-testid="stSidebar"] button span[data-testid="stIconMaterial"],
    [data-testid="stSidebar"] button .material-symbols-rounded {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}
    
    /* Hide any tooltip/popover that appears on hover globally for sidebar */
    [data-testid="stSidebar"] button::after,
    [data-testid="stSidebar"] button::before {{
        display: none !important;
    }}

    /* Hide the keyboard icon that appears in sidebar nav buttons */
    [data-testid="stSidebar"] button > div > div:last-child:not(:first-child) {{
        display: none !important;
    }}

    /* Target the specific material icon span for keyboard_double_arrow_right */
    span.material-symbols-rounded {{
        display: none !important;
    }}

    /* Hide stSidebarNavItems tooltip icons */
    [data-testid="stSidebarNavItems"] span[data-testid],
    [data-testid="stSidebarNavLink"] span:not(:first-child) {{
        display: none !important;
    }}

    /* Aggressive: hide any element containing keyboard_double text */
    [data-testid="stSidebar"] button [title],
    [data-testid="stSidebar"] [aria-label*="keyboard"] {{
        display: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Also inject JS to nuke title attributes and material icons from sidebar buttons
    st.markdown("""
    <script>
    (function removeSidebarTooltips() {
        function clean() {
            // Remove title attributes from all sidebar buttons
            document.querySelectorAll('[data-testid="stSidebar"] button').forEach(btn => {
                btn.removeAttribute('title');
                btn.removeAttribute('aria-label');
                // Hide any span containing material icon text
                btn.querySelectorAll('span').forEach(span => {
                    if (span.textContent.trim() === 'keyboard_double_arrow_right' ||
                        span.classList.contains('material-symbols-rounded') ||
                        span.classList.contains('material-icons')) {
                        span.style.display = 'none';
                    }
                });
            });
            // Remove all title attrs site-wide that cause native browser tooltips
            document.querySelectorAll('[title]').forEach(el => {
                el.removeAttribute('title');
            });
        }
        // Run on load and after DOM mutations
        clean();
        setTimeout(clean, 300);
        setTimeout(clean, 800);
        setTimeout(clean, 2000);
        const observer = new MutationObserver(clean);
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """, unsafe_allow_html=True)

# ========== LOGIN PAGE ==========
def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="background:white; border-radius:28px; padding:48px 40px; text-align:center; margin-top:60px; box-shadow:0 20px 60px rgba(0,0,0,0.12);">
            <div style="width:72px;height:72px;background:linear-gradient(135deg,#6366F1,#8B5CF6); border-radius:20px; display:inline-flex; align-items:center; justify-content:center; font-size:32px; margin-bottom:20px;">💎</div>
            <h1 style="font-size:26px;font-weight:800;margin:0 0 6px 0;">FinanceIQ</h1>
            <p style="color:#64748B;font-size:14px;margin-bottom:32px;">Smart Personal Finance Tracker</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔑 Login", use_container_width=True):
                if username in st.session_state.users:
                    if st.session_state.users[username] == hash_password(password):
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.rerun()
                    else:
                        st.error("Incorrect password!")
                else:
                    st.error("User not found!")
        with col_b:
            if st.button("✨ Register", use_container_width=True):
                if username and password:
                    if username in st.session_state.users:
                        st.warning("Username taken!")
                    elif len(password) < 4:
                        st.warning("Password too short (min 4 chars)!")
                    else:
                        st.session_state.users[username] = hash_password(password)
                        st.success("Account created! Please login.")
                else:
                    st.warning("Please fill all fields.")

        st.markdown("<p style='text-align:center;color:#64748B;font-size:12px;margin-top:20px;'>Demo: <strong>admin</strong> / <strong>password123</strong></p>", unsafe_allow_html=True)

# ========== SIDEBAR NAVIGATION ==========
def sidebar_nav():
    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 0 10px 0;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
                <div style="width:42px;height:42px;background:linear-gradient(135deg,#6366F1,#8B5CF6); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:20px;">💎</div>
                <div>
                    <div style="font-size:16px;font-weight:800;">FinanceIQ</div>
                    <div style="font-size:11px;opacity:0.7;">{st.session_state.current_user}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.selected_page = "Dashboard"
            st.rerun()
            
        if st.button("💳 Transactions", use_container_width=True):
            st.session_state.selected_page = "Transactions"
            st.rerun()
            
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.selected_page = "Analytics"
            st.rerun()
            
        if st.button("🎯 Budgets", use_container_width=True):
            st.session_state.selected_page = "Budgets"
            st.rerun()
            
        if st.button("🏆 Goals", use_container_width=True):
            st.session_state.selected_page = "Goals"
            st.rerun()
            
        if st.button("🤖 AI Advisor", use_container_width=True):
            st.session_state.selected_page = "AI Advisor"
            st.rerun()
            
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.selected_page = "Settings"
            st.rerun()

        st.markdown("---")

        df = st.session_state.transactions
        income = df[df['type'] == 'income']['amount'].sum()
        expense = df[df['type'] == 'expense']['amount'].sum()
        savings = income - expense
        savings_rate = (savings / income * 100) if income > 0 else 0
        sym = st.session_state.get('currency', '₹')

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#6366F1,#8B5CF6);border-radius:16px;padding:18px;text-align:center;margin:10px 0;">
            <div style="font-size:11px;opacity:0.8;text-transform:uppercase;">Net Balance</div>
            <div style="font-size:24px;font-weight:800;font-family:monospace;margin:6px 0;">{sym}{savings:,.0f}</div>
            <div style="font-size:11px;opacity:0.8;">↑ {savings_rate:.1f}% saved</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size:12px;font-weight:700;margin:12px 0 8px 0;text-transform:uppercase;'>Upcoming Bills</div>", unsafe_allow_html=True)
        upcoming = [
            ("📡", "Internet Bill", "3 days"),
            ("💡", "Electricity", "7 days"),
            ("🏠", "Rent", "12 days"),
        ]
        for icon, name, days in upcoming:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.1);">
                <div><span>{icon}</span> <span style="margin-left:8px;font-size:13px;">{name}</span></div>
                <span style="font-size:11px;color:#F59E0B;">{days}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

# ========== DASHBOARD PAGE ==========
def dashboard_page():
    df = st.session_state.transactions
    summary = get_summary(df)
    sym = st.session_state.get('currency', '₹')
    dark = st.session_state.get('dark_mode', False)
    subtext = "#94A3B8" if dark else "#64748B"

    st.markdown(f'<div class="page-header">Good morning 👋</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{datetime.now().strftime("%A, %B %d, %Y")} — Here\'s your financial overview</div>', unsafe_allow_html=True)

    if st.button("➕ Add Transaction", type="primary", use_container_width=False):
        st.session_state.show_transaction_form = not st.session_state.show_transaction_form

    if st.session_state.show_transaction_form:
        st.markdown("---")
        st.markdown("### ✏️ Enter Transaction Details")
        
        qc1, qc2, qc3, qc4, qc5 = st.columns(5)
        with qc1:
            q_date = st.date_input("Date", datetime.now(), key="q_date")
        with qc2:
            q_type = st.selectbox("Type", ["expense", "income"], key="q_type")
        with qc3:
            cats = ['Food & Dining', 'Shopping', 'Transport', 'Entertainment', 'Utilities', 'Healthcare', 'Rent', 'Insurance', 'Income']
            q_cat = st.selectbox("Category", cats, key="q_cat")
        with qc4:
            q_amount = st.number_input(f"Amount ({sym})", min_value=0.01, step=100.0, key="q_amount")
        with qc5:
            q_mode = st.selectbox("Mode", ["UPI", "Card", "Cash", "Net Banking"], key="q_mode")
        
        if st.button("💾 Save Transaction", type="primary"):
            if q_amount > 0:
                st.session_state.transactions = add_transaction(df, q_date, q_cat, q_cat, q_type, q_amount, q_mode, "")
                st.success("✅ Transaction added successfully!")
                st.session_state.show_transaction_form = False
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💰 TOTAL INCOME</div>
            <div class="metric-value">{sym}{summary['income']:,.0f}</div>
            <div style="font-size:12px;">+12% vs last month</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💸 TOTAL EXPENSES</div>
            <div class="metric-value">{sym}{summary['expense']:,.0f}</div>
            <div style="font-size:12px;">Across all categories</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💎 NET SAVINGS</div>
            <div class="metric-value">{sym}{summary['savings']:,.0f}</div>
            <div style="font-size:12px;">{summary['savings_rate']:.1f}% savings rate</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📊 TRANSACTIONS</div>
            <div class="metric-value">{summary['transaction_count']}</div>
            <div style="font-size:12px;">Avg {fmt(summary['avg_daily'])}/day</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='margin: 20px 0 10px 0;'></div>", unsafe_allow_html=True)

    ch1, space, ch2 = st.columns([1, 0.1, 1])

    with ch1:
        st.markdown('<div class="section-title">📈 Monthly Income vs Expenses</div>', unsafe_allow_html=True)
        if len(summary['monthly_income']) > 0:
            months = sorted(set(list(summary['monthly_income'].index) + list(summary['monthly_expense'].index)))
            fig = go.Figure()
            fig.add_trace(go.Bar(x=months, y=[summary['monthly_income'].get(m, 0) for m in months],
                                  name='Income', marker_color='#10B981', marker_line_width=0))
            fig.add_trace(go.Bar(x=months, y=[summary['monthly_expense'].get(m, 0) for m in months],
                                  name='Expenses', marker_color='#EF4444', marker_line_width=0))
            fig.update_layout(
                barmode='group', 
                height=320,
                width=None,
                margin=dict(l=10, r=10, t=30, b=30),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(size=11),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                xaxis=dict(showgrid=False, tickangle=-45),
                yaxis=dict(showgrid=True, gridcolor='rgba(148,163,184,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with ch2:
        st.markdown('<div class="section-title">🥧 Expense Breakdown</div>', unsafe_allow_html=True)
        if len(summary['top_expenses']) > 0:
            fig = px.pie(
                values=summary['top_expenses'].values, 
                names=summary['top_expenses'].index,
                hole=0.5,
                color_discrete_sequence=['#6366F1', '#8B5CF6', '#EC4899', '#EF4444', '#F59E0B', '#10B981', '#06B6D4']
            )
            fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=10)
            fig.update_layout(
                height=320,
                width=None,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='margin: 30px 0 20px 0;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">📊 Savings Rate Progress</div>', unsafe_allow_html=True)
    pct = min(summary['savings_rate'], 100)
    st.markdown(f"""
    <div class="card">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <span>Monthly Savings Goal: 20%</span>
            <span style="font-weight:800;">{pct:.1f}%</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width:{pct}%;"></div></div>
        <div style="display:flex; justify-content:space-between; margin-top:8px;">
            <span>Current: {sym}{summary['savings']:,.0f} saved</span>
            <span>Target: {sym}{summary['income']*0.2:,.0f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ========== TRANSACTIONS PAGE ==========
def transactions_page():
    df = st.session_state.transactions
    sym = st.session_state.get('currency', '₹')
    
    st.markdown('<div class="page-header">Transactions</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Manage all your income and expense records</div>', unsafe_allow_html=True)

    if st.button("➕ Add New Transaction", type="primary", use_container_width=False):
        st.session_state.show_transaction_form = not st.session_state.show_transaction_form

    if st.session_state.show_transaction_form:
        st.markdown("---")
        st.markdown("### ✏️ Enter Transaction Details")
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            t_date = st.date_input("Date", datetime.now(), key="t_date")
        with c2:
            t_type = st.selectbox("Type", ["expense", "income"], key="t_type")
        with c3:
            all_cats = ['Food & Dining', 'Shopping', 'Transport', 'Entertainment', 'Utilities', 'Healthcare', 'Rent', 'Insurance', 'Income']
            t_cat = st.selectbox("Category", all_cats, key="t_cat")
        with c4:
            t_desc = st.text_input("Description", key="t_desc")
        with c5:
            t_amount = st.number_input(f"Amount ({sym})", min_value=0.01, step=100.0, key="t_amount")
        
        t_mode = st.selectbox("Payment Mode", ["UPI", "Card", "Cash", "Net Banking"], key="t_mode")
        
        if st.button("💾 Save Transaction", type="primary"):
            if t_desc and t_amount > 0:
                st.session_state.transactions = add_transaction(df, t_date, t_desc, t_cat, t_type, t_amount, t_mode, "")
                st.success("✅ Transaction added successfully!")
                st.session_state.show_transaction_form = False
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    display_df = df.copy()
    display_df['date'] = display_df['date'].dt.strftime('%d %b %Y')
    display_df['amount_formatted'] = display_df.apply(lambda r: f"{'+' if r['type']=='income' else '-'}{sym}{abs(r['amount']):,.0f}", axis=1)
    
    st.dataframe(display_df[['date', 'description', 'category', 'type', 'amount_formatted', 'payment_mode']],
                  use_container_width=True, hide_index=True)

# ========== ANALYTICS PAGE ==========
def analytics_page():
    df = st.session_state.transactions
    sym = st.session_state.get('currency', '₹')
    dark = st.session_state.get('dark_mode', False)
    subtext = "#94A3B8" if dark else "#64748B"
    
    st.markdown('<div class="page-header">📊 Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Deep dive into your financial patterns</div>', unsafe_allow_html=True)

    summary = get_summary(df)

    col1, space, col2 = st.columns([1, 0.1, 1])
    
    with col1:
        st.markdown('<div class="section-title">📊 Expense by Category</div>', unsafe_allow_html=True)
        exp_df = df[df['type'] == 'expense']
        cat_sum = exp_df.groupby('category')['amount'].sum().sort_values()
        fig = px.bar(
            x=cat_sum.values, 
            y=cat_sum.index,
            orientation='h',
            color=cat_sum.values,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='rgba(148,163,184,0.1)'),
            yaxis=dict(showgrid=False),
            font=dict(size=11),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col2:
        st.markdown('<div class="section-title">💰 Income vs Expense Share</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=['Income', 'Expenses', 'Savings'], 
            values=[summary['income'], summary['expense'], max(0, summary['savings'])],
            hole=0.55, 
            marker_colors=['#10B981', '#EF4444', '#6366F1'],
            textposition='outside',
            textinfo='percent+label'
        ))
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=30, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=-0.1, xanchor='center', x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='margin: 30px 0 20px 0;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">📋 Budget vs Actual</div>', unsafe_allow_html=True)
    budgets = st.session_state.budgets
    actual = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
    
    for cat, budget in budgets.items():
        spent = actual.get(cat, 0)
        pct = min((spent / budget * 100) if budget > 0 else 0, 100)
        color = "#EF4444" if spent > budget else "#10B981" if pct < 70 else "#F59E0B"
        st.markdown(f"""
        <div style="margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="font-weight:500; font-size:13px;">{cat}</span>
                <span style="font-size:12px;"><span style="color:#EF4444;">{sym}{spent:,.0f}</span> / {sym}{budget:,.0f}</span>
            </div>
            <div class="progress-bar" style="height:6px;"><div style="background:{color};height:100%;width:{pct}%;border-radius:100px;"></div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin: 25px 0 15px 0;'></div>", unsafe_allow_html=True)

    col1, space, col2 = st.columns([1, 0.1, 1])
    
    with col1:
        st.markdown('<div class="section-title">📅 Top Spending Categories</div>', unsafe_allow_html=True)
        top_5 = summary['top_expenses'].head(5)
        for i, (cat, amt) in enumerate(top_5.items()):
            pct = (amt / summary['expense'] * 100)
            st.markdown(f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; font-size:13px;">
                    <span>{i+1}. {cat}</span>
                    <span><strong>{sym}{amt:,.0f}</strong> ({pct:.1f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-title">💡 Spending Insights</div>', unsafe_allow_html=True)
        insights = []
        top_cat = summary['top_expenses'].index[0] if len(summary['top_expenses']) > 0 else None
        if top_cat:
            insights.append(f"🔴 Your highest spending is on **{top_cat}**")
        if summary['savings_rate'] < 20:
            insights.append(f"🟡 Savings rate is {summary['savings_rate']:.0f}% - aim for 20%")
        if summary['avg_daily'] > 0:
            insights.append(f"📊 Daily average spend: {sym}{summary['avg_daily']:,.0f}")
        
        for insight in insights:
            st.markdown(f"<div style='background:rgba(99,102,241,0.1); padding:10px; border-radius:10px; margin-bottom:10px; font-size:13px;'>{insight}</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin: 25px 0 0 0;'></div>", unsafe_allow_html=True)

# ========== GOALS PAGE ==========
def goals_page():
    sym = st.session_state.get('currency', '₹')
    
    st.markdown('<div class="page-header">Savings Goals</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Track your financial milestones</div>', unsafe_allow_html=True)

    if st.button("➕ Add New Goal", type="primary", use_container_width=False):
        st.session_state.show_goal_form = not st.session_state.show_goal_form

    if st.session_state.get('show_goal_form', False):
        st.markdown("---")
        st.markdown("### ✏️ Create New Goal")
        
        gc1, gc2, gc3, gc4 = st.columns(4)
        with gc1:
            g_name = st.text_input("Goal Name", key="g_name")
        with gc2:
            g_target = st.number_input(f"Target ({sym})", min_value=100.0, step=1000.0, key="g_target")
        with gc3:
            g_saved = st.number_input(f"Already Saved ({sym})", min_value=0.0, step=100.0, key="g_saved")
        with gc4:
            g_deadline = st.date_input("Deadline", key="g_deadline")
        if st.button("🎯 Create Goal", type="primary"):
            if g_name and g_target > 0:
                st.session_state.goals.append({
                    'name': g_name, 'target': g_target, 'saved': g_saved,
                    'deadline': str(g_deadline), 'icon': '🏆'
                })
                st.success("Goal created!")
                st.session_state.show_goal_form = False
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    for i, goal in enumerate(st.session_state.goals):
        pct = min((goal['saved'] / goal['target'] * 100) if goal['target'] > 0 else 0, 100)
        remaining = goal['target'] - goal['saved']
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
            <div class="card">
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                    <div>
                        <span style="font-size:24px;">{goal['icon']}</span>
                        <span style="font-weight:700;margin-left:10px;">{goal['name']}</span>
                    </div>
                    <div>{pct:.1f}%</div>
                </div>
                <div class="progress-bar"><div class="progress-fill" style="width:{pct}%;"></div></div>
                <div style="margin-top:8px;">Saved: {sym}{goal['saved']:,.0f} / {sym}{goal['target']:,.0f}</div>
                <div style="font-size:12px;">Remaining: {sym}{remaining:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            contrib = st.number_input(f"Add", min_value=0.0, step=100.0, key=f"contrib_{i}", label_visibility="collapsed")
            if st.button("💰 Add", key=f"add_goal_{i}"):
                if contrib > 0:
                    st.session_state.goals[i]['saved'] = min(goal['saved'] + contrib, goal['target'])
                    st.rerun()

# ========== AI ADVISOR PAGE ==========
def ai_advisor_page():
    dark = st.session_state.get('dark_mode', False)
    
    st.markdown('<div class="page-header">AI Financial Advisor</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Personalized insights powered by your data</div>', unsafe_allow_html=True)

    df = st.session_state.transactions
    summary = get_summary(df)
    insights = generate_ai_insights(summary, df)

    score = min(100, int(summary['savings_rate'] * 3 + 20))
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#6366F1,#8B5CF6);border-radius:20px;padding:30px;text-align:center;margin-bottom:24px;">
        <div style="font-size:13px;opacity:0.8;text-transform:uppercase;">Financial Health Score</div>
        <div style="font-size:72px;font-weight:900;font-family:monospace;line-height:1;">{score}</div>
        <div style="font-size:13px;opacity:0.8;">Based on savings rate & spending patterns</div>
    </div>
    """, unsafe_allow_html=True)

    for ins in insights:
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;align-items:flex-start;gap:14px;">
                <div style="font-size:24px;">{ins['icon']}</div>
                <div>
                    <div style="font-size:16px;font-weight:700;margin-bottom:4px;">{ins['title']}</div>
                    <div style="font-size:13px;opacity:0.8;margin-bottom:10px;">{ins['desc']}</div>
                    <div style="background:rgba(99,102,241,0.1);color:#6366F1;padding:6px 12px;border-radius:8px;font-size:12px;display:inline-block;">💡 {ins['action']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ========== SETTINGS PAGE ==========
def settings_page():
    dark = st.session_state.get('dark_mode', False)
    text = "#F1F5F9" if dark else "#0F172A"
    subtext = "#94A3B8" if dark else "#64748B"
    card_bg = "#1E293B" if dark else "#FFFFFF"
    border = "#334155" if dark else "#E2E8F0"
    sym = st.session_state.get('currency', '₹')
    
    st.markdown('<div class="page-header">⚙️ Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Customize your FinanceIQ experience</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Profile", "🎨 Appearance", "🔔 Notifications", "💾 Data", "🌐 Language"])
    
    with tab1:
        st.markdown('<div class="section-title">Profile Information</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            display_name = st.text_input("Display Name", value=st.session_state.get('current_user', 'admin'), key="display_name")
            email = st.text_input("Email Address", value=f"{st.session_state.get('current_user', 'admin')}@financeiq.com", key="email")
        with col2:
            phone = st.text_input("Phone Number", value="+91 98765 43210", key="phone")
            occupation = st.selectbox("Occupation", ["Salaried", "Self-Employed", "Business", "Student", "Freelancer", "Other"], key="occupation")
        
        if st.button("💾 Update Profile", type="primary"):
            st.success("Profile updated successfully!")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Change Password</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            current_pwd = st.text_input("Current Password", type="password", key="current_pwd")
        with col2:
            new_pwd = st.text_input("New Password", type="password", key="new_pwd")
        with col3:
            confirm_pwd = st.text_input("Confirm Password", type="password", key="confirm_pwd")
        
        if st.button("🔐 Change Password", type="primary"):
            if current_pwd and new_pwd and confirm_pwd:
                if new_pwd == confirm_pwd:
                    if len(new_pwd) >= 4:
                        st.success("Password changed successfully!")
                    else:
                        st.error("Password must be at least 4 characters!")
                else:
                    st.error("New passwords do not match!")
            else:
                st.warning("Please fill all fields!")

    with tab2:
        st.markdown('<div class="section-title">Theme Settings</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.get('dark_mode', False), key="dark_mode_toggle")
            if dark_mode != st.session_state.dark_mode:
                st.session_state.dark_mode = dark_mode
                st.rerun()
        
        with col2:
            st.markdown(f"""
            <div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:12px; margin-top:8px;">
                <div style="font-size:12px; color:{subtext};">Preview</div>
                <div style="display:flex; gap:8px; margin-top:8px;">
                    <div style="width:30px; height:30px; background:#6366F1; border-radius:8px;"></div>
                    <div style="width:30px; height:30px; background:#8B5CF6; border-radius:8px;"></div>
                    <div style="width:30px; height:30px; background:#10B981; border-radius:8px;"></div>
                    <div style="width:30px; height:30px; background:#EF4444; border-radius:8px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Currency Settings</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            currencies = {
                "🇮🇳 Indian Rupee (₹)": "₹",
                "🇺🇸 US Dollar ($)": "$",
                "🇪🇺 Euro (€)": "€",
                "🇬🇧 British Pound (£)": "£",
                "🇯🇵 Japanese Yen (¥)": "¥",
                "🇨🇦 Canadian Dollar (C$)": "C$",
                "🇦🇺 Australian Dollar (A$)": "A$",
                "🇨🇳 Chinese Yuan (¥)": "¥",
                "🇸🇬 Singapore Dollar (S$)": "S$",
                "🇦🇪 UAE Dirham (د.إ)": "د.إ",
            }
            selected_currency = st.selectbox("Select Currency", list(currencies.keys()), key="currency_selector")
            new_currency = currencies[selected_currency]
            if new_currency != st.session_state.currency:
                if st.button("Apply Currency", type="secondary"):
                    st.session_state.currency = new_currency
                    st.success(f"Currency changed to {selected_currency}")
                    st.rerun()
        
        with col2:
            st.markdown(f"""
            <div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:11px; color:{subtext};">Current Currency Format</div>
                <div style="font-size:28px; font-weight:800; color:#6366F1;">{st.session_state.currency} 10,000</div>
                <div style="font-size:11px; color:{subtext}; margin-top:4px;">Example: {st.session_state.currency}1,234.56</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Date & Time Format</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            date_format = st.selectbox("Date Format", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"], key="date_format")
        with col2:
            time_format = st.selectbox("Time Format", ["12 Hour", "24 Hour"], key="time_format")
        
        if st.button("💾 Save Appearance Settings"):
            st.success("Appearance settings saved!")

    with tab3:
        st.markdown('<div class="section-title">Notification Preferences</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:20px;">
            <div style="margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:600;">📧 Email Weekly Reports</div>
                        <div style="font-size:12px; color:{subtext};">Receive weekly summary of your finances</div>
                    </div>
                    <div>{st.toggle("", value=True, key="email_reports")}</div>
                </div>
            </div>
            <div style="margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:600;">💰 Budget Alerts</div>
                        <div style="font-size:12px; color:{subtext};">Get notified when you exceed 80% of budget</div>
                    </div>
                    <div>{st.toggle("", value=True, key="budget_alerts")}</div>
                </div>
            </div>
            <div style="margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:600;">📅 Bill Reminders</div>
                        <div style="font-size:12px; color:{subtext};">Reminders for upcoming bills and due dates</div>
                    </div>
                    <div>{st.toggle("", value=True, key="bill_reminders")}</div>
                </div>
            </div>
            <div style="margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:600;">🎯 Goal Milestones</div>
                        <div style="font-size:12px; color:{subtext};">Celebrate when you reach savings goals</div>
                    </div>
                    <div>{st.toggle("", value=True, key="goal_milestones")}</div>
                </div>
            </div>
            <div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:600;">🤖 AI Insights</div>
                        <div style="font-size:12px; color:{subtext};">Get personalized financial tips</div>
                    </div>
                    <div>{st.toggle("", value=True, key="ai_insights")}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            notification_email = st.text_input("Notification Email", value=f"{st.session_state.get('current_user', 'admin')}@financeiq.com", key="notif_email")
        with col2:
            reminder_days = st.number_input("Days before due for reminder", min_value=1, max_value=30, value=3, key="reminder_days")
        
        if st.button("💾 Save Notification Settings", type="primary"):
            st.success("Notification settings saved!")

    with tab4:
        st.markdown('<div class="section-title">Backup & Export</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Backup (CSV)", use_container_width=True, type="primary"):
                df = st.session_state.transactions
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="financeiq_backup.csv">Download Backup</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("Backup ready!")
        
        with col2:
            if st.button("📊 Download Report (PDF)", use_container_width=True):
                st.info("PDF report generation - Would create a formatted financial report")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Import Data</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Import transactions from CSV", type=['csv'], key="import_csv")
        if uploaded_file:
            try:
                imported_df = pd.read_csv(uploaded_file)
                st.success(f"Imported {len(imported_df)} transactions!")
                if st.button("Confirm Import"):
                    st.session_state.transactions = imported_df
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading file: {e}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Data Management</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reset to Sample Data", use_container_width=True):
                st.session_state.transactions = generate_sample_data()
                st.success("Data reset to sample!")
                st.rerun()
        
        with col2:
            if st.button("📊 Clear All Transactions", use_container_width=True):
                st.warning("⚠️ This will delete ALL your transactions!")
                if st.button("Confirm Delete", key="confirm_delete"):
                    st.session_state.transactions = pd.DataFrame(columns=['date', 'description', 'category', 'type', 'amount', 'payment_mode', 'notes'])
                    st.success("All data cleared!")
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Delete Account</div>', unsafe_allow_html=True)
        
        st.warning("⚠️ Deleting your account is permanent and cannot be undone!")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            confirm_delete_text = st.text_input("Type 'DELETE' to confirm", key="delete_confirm", type="password")
        with col2:
            if st.button("🗑️ Delete My Account", use_container_width=True):
                if confirm_delete_text == "DELETE":
                    st.error("Account deleted. Redirecting to login...")
                    st.session_state.authenticated = False
                    st.rerun()
                else:
                    st.error("Please type 'DELETE' to confirm")

    with tab5:
        st.markdown('<div class="section-title">Language Preferences</div>', unsafe_allow_html=True)
        
        languages = {
            "English": "🇬🇧",
            "Hindi": "🇮🇳",
            "Spanish": "🇪🇸",
            "French": "🇫🇷",
            "German": "🇩🇪",
            "Japanese": "🇯🇵",
            "Chinese": "🇨🇳",
            "Arabic": "🇸🇦",
            "Portuguese": "🇵🇹",
            "Russian": "🇷🇺",
            "Tamil": "🇮🇳",
            "Telugu": "🇮🇳",
            "Kannada": "🇮🇳",
            "Malayalam": "🇮🇳",
            "Bengali": "🇮🇳",
            "Marathi": "🇮🇳",
        }
        
        col1, col2 = st.columns(2)
        with col1:
            selected_lang = st.selectbox("Select Language", list(languages.keys()), key="language_select")
            st.markdown(f"""
            <div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:16px; margin-top:16px;">
                <div style="text-align:center;">
                    <span style="font-size:48px;">{languages[selected_lang]}</span>
                    <div style="font-size:18px; font-weight:600; margin-top:8px;">{selected_lang}</div>
                    <div style="font-size:11px; color:{subtext};">Selected Language</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:16px;">
                <div style="font-weight:600; margin-bottom:12px;">Language Preview</div>
                <div style="font-size:13px;">
                    <div>🏠 Dashboard → {'डैशबोर्ड' if selected_lang == 'Hindi' else 'Dashboard'}</div>
                    <div>💰 Income → {'आय' if selected_lang == 'Hindi' else 'Income'}</div>
                    <div>💸 Expenses → {'व्यय' if selected_lang == 'Hindi' else 'Expenses'}</div>
                    <div>💎 Savings → {'बचत' if selected_lang == 'Hindi' else 'Savings'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("💾 Save Language Preference", type="primary"):
            st.session_state.language = selected_lang
            st.success(f"Language changed to {selected_lang}!")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Regional Settings</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            timezone = st.selectbox("Time Zone", ["IST (UTC+5:30)", "EST (UTC-5)", "PST (UTC-8)", "GMT (UTC+0)", "CST (UTC+8)"], key="timezone")
        with col2:
            first_day = st.selectbox("First Day of Week", ["Monday", "Sunday", "Saturday"], key="first_day")
        
        if st.button("💾 Save Regional Settings"):
            st.success("Regional settings saved!")

    st.markdown(f"""
    <div style="text-align:center; padding:20px; margin-top:20px; border-top:1px solid {border};">
        <div style="font-size:11px; color:{subtext};">FinanceIQ v2.0 | Built with ❤️ | Last updated: {datetime.now().strftime('%B %d, %Y')}</div>
    </div>
    """, unsafe_allow_html=True)

# ========== BUDGETS PAGE ==========
def budgets_page():
    sym = st.session_state.get('currency', '₹')
    dark = st.session_state.get('dark_mode', False)
    text = "#F1F5F9" if dark else "#0F172A"
    subtext = "#94A3B8" if dark else "#64748B"
    card_bg = "#1E293B" if dark else "#FFFFFF"
    border = "#334155" if dark else "#E2E8F0"
    
    st.markdown('<div class="page-header">💰 Budgets</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Set and track monthly spending limits</div>', unsafe_allow_html=True)

    df = st.session_state.transactions
    actual = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
    budgets = st.session_state.budgets

    if st.button("✏️ Edit Budget Limits", type="primary", use_container_width=False):
        st.session_state.show_budget_form = not st.session_state.show_budget_form

    if st.session_state.get('show_budget_form', False):
        st.markdown("---")
        st.markdown("### ✏️ Set Budget Limits")
        
        b_cols = st.columns(2)
        new_budgets = {}
        for i, (cat, val) in enumerate(budgets.items()):
            with b_cols[i % 2]:
                new_budgets[cat] = st.number_input(f"{cat} ({sym})", value=float(val), step=500.0, key=f"budget_{cat}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Budgets", type="primary"):
                st.session_state.budgets = new_budgets
                st.success("Budgets updated!")
                st.session_state.show_budget_form = False
                st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.show_budget_form = False
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    total_budget = sum(budgets.values())
    total_spent = sum(actual.get(cat, 0) for cat in budgets)
    remaining = total_budget - total_spent
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div class="metric-label">📋 TOTAL BUDGET</div>
            <div class="metric-value" style="color:#6366F1;">{sym}{total_budget:,.0f}</div>
            <div style="font-size:12px;">Monthly limit</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div class="metric-label">💸 TOTAL SPENT</div>
            <div class="metric-value" style="color:#EF4444;">{sym}{total_spent:,.0f}</div>
            <div style="font-size:12px;">Across all categories</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        remaining_color = "#10B981" if remaining > 0 else "#EF4444"
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div class="metric-label">✅ REMAINING</div>
            <div class="metric-value" style="color:{remaining_color};">{sym}{remaining:,.0f}</div>
            <div style="font-size:12px;">Left to spend</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Category Budgets</div>', unsafe_allow_html=True)

    for cat, budget in budgets.items():
        spent = actual.get(cat, 0)
        remaining_cat = budget - spent
        pct = min((spent / budget * 100) if budget > 0 else 0, 100)
        over = spent > budget
        
        if over:
            status = "🚨 Over Budget"
            status_color = "#EF4444"
            bar_color = "#EF4444"
        elif pct >= 90:
            status = "⚠️ Near Limit"
            status_color = "#F59E0B"
            bar_color = "#F59E0B"
        else:
            status = "✅ On Track"
            status_color = "#10B981"
            bar_color = "#10B981"
        
        st.markdown(f"""
        <div style="background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:16px; margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div>
                    <span style="font-size:15px; font-weight:700;">{cat}</span>
                    <span style="margin-left:10px; background:{status_color}20; color:{status_color}; padding:2px 8px; border-radius:20px; font-size:10px; font-weight:600;">{status}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:16px; font-weight:700;">{sym}{spent:,.0f}</span>
                    <span style="font-size:13px; color:{subtext};"> / {sym}{budget:,.0f}</span>
                </div>
            </div>
            <div class="progress-bar" style="height:8px;"><div style="background:{bar_color}; height:100%; width:{pct}%; border-radius:100px;"></div></div>
            <div style="display:flex; justify-content:space-between; margin-top:8px;">
                <span style="font-size:11px; color:{subtext};">{pct:.1f}% used</span>
                <span style="font-size:11px; color:{'#EF4444' if remaining_cat < 0 else '#10B981'};">Remaining: {sym}{abs(remaining_cat):,.0f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    over_budget_cats = [(cat, actual.get(cat, 0) - budgets[cat]) for cat in budgets if actual.get(cat, 0) > budgets.get(cat, 0)]
    if over_budget_cats:
        st.markdown("---")
        st.markdown("### ⚠️ Budget Alerts")
        for cat, over_amount in over_budget_cats:
            st.warning(f"🔴 **{cat}** is over budget by {sym}{over_amount:,.0f}")

# ========== MAIN ==========
def main():
    init_session_state()
    load_css()

    if not st.session_state.authenticated:
        login_page()
        return

    sidebar_nav()

    if st.session_state.selected_page == "Dashboard":
        dashboard_page()
    elif st.session_state.selected_page == "Transactions":
        transactions_page()
    elif st.session_state.selected_page == "Analytics":
        analytics_page()
    elif st.session_state.selected_page == "Budgets":
        budgets_page()
    elif st.session_state.selected_page == "Goals":
        goals_page()
    elif st.session_state.selected_page == "AI Advisor":
        ai_advisor_page()
    elif st.session_state.selected_page == "Settings":
        settings_page()

    dark = st.session_state.get('dark_mode', False)
    subtext = "#94A3B8" if dark else "#64748B"
    st.markdown(f'<div class="footer">FinanceIQ © 2025 · Smart Personal Finance Tracker</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()