import streamlit as st

# -----------------------------
# Basic page config
# -----------------------------
st.set_page_config(page_title="Blis Measurement Wizard", layout="centered")

# -----------------------------
# Market & currency settings
# -----------------------------
MARKETS = {
    "US": {"currency_symbol": "$", "currency_name": "USD"},
    "UK": {"currency_symbol": "£", "currency_name": "GBP"},
    "India": {"currency_symbol": "₹", "currency_name": "INR"},
    "EU": {"currency_symbol": "€", "currency_name": "EUR"},
    "Other": {"currency_symbol": "", "currency_name": "Local currency"},
}


def get_budget_band_labels(market_info: dict):
    """Return human-readable budget bands using the market currency."""
    cur = market_info["currency_symbol"]
    # If we don't know the symbol, just say "local currency"
    if cur == "":
        low = "Low (small test budget)"
        med = "Medium (standard campaign)"
        high = "High (large, flagship campaign)"
    else:
        low = f"Low ({cur}0–{cur}50k)"
        med = f"Medium ({cur}50k–{cur}150k)"
        high = f"High ({cur}150k+)"
    return [low, med, high]


def get_budget_level(budget_label: str) -> str:
    """Map label back to 'Low' / 'Medium' / 'High'."""
    label = budget_label.lower()
    if "low" in label:
        return "Low"
    if "high" in label:
        return "High"
    return "Medium"


def get_impression_level(imp_label: str) -> str:
    """Very rough categorisation of impression bands."""
    label = imp_label.lower()
    if "<" in label or "0–" in label:
        return "Low"
    if "100k–" in label or "50k–" in label:
        return "Medium"
    return "High"


# -----------------------------
# Feasibility scoring
# -----------------------------
def compute_feasibility_score(answers: dict) -> int:
    """
    Start from 3 and subtract points for risk factors.
    3+  -> strong
    2   -> feasible with caveats
    1   -> borderline / directional
    0-  -> not recommended as formal study
    """
    score = 3

    if answers["budget_level"] == "Low":
        score -= 1
    if answers["impressions_level"] == "Low":
        score -= 1
    if answers["duration"] in ["< 1 week", "1–2 weeks"]:
        score -= 1
    if (
        answers["objective"] == "Brand awareness / consideration"
        and answers["ids"] == "No"
    ):
        score -= 1
    if (
        answers["objective"] in ["Footfall / store visits", "Sales / conversions"]
        and answers["offline_data"] == "No"
    ):
        score -= 1

    return score


def map_score_to_status(score: int) -> tuple[str, str]:
    """
    Map numeric score to a human label + streamlit message type.
      returns: (status_text, status_type)
      where status_type is one of 'success', 'warning', 'error'
    """
    if score >= 3:
        return "Strong measurement feasible", "success"
    if score == 2:
        return "Feasible but with caveats", "warning"
    if score == 1:
        return "Borderline – treat as directional only", "warning"
    return "Not recommended as a formal study – directional only", "error"


# -----------------------------
# Recommendation logic
# -----------------------------
def build_recommendation(answers: dict) -> dict:
    """
    Very simple rules-based engine.
    Returns a dict with:
      - primary
      - details (list of strings)
      - risks (list of strings)
      - alternatives (list of strings)
      - methods (list of strings)  # for analysts
    """
    objective = answers["objective"]
    ids = answers["ids"]
    budget_level = answers["budget_level"]
    impressions_level = answers["impressions_level"]
    duration = answers["duration"]
    control = answers["control"]
    offline_data = answers["offline_data"]
    market = answers["market"]

    primary = ""
    details = []
    risks = []
    alternatives = []
    methods = []

    # --- Objective-specific recommendations ---

    if objective == "Brand awareness / consideration":
        if ids == "Yes":
            primary = "Run an ID-based Brand Lift Study where available."
            methods.append("Full Brand Lift Study (ID-based or panel, exposed vs control)")
            details.append(
                "Use exposed vs control methodology with IDs or device-based panels, "
                "following local market norms."
            )
        else:
            primary = "Use a panel-based Brand Lift or directional brand proxies."
            methods.append("Panel-based Brand Lift or survey add-on")
            methods.append("Directional brand proxy: CTR, VTR, attention metrics")
            details.append(
                "Without IDs, use survey panels or brand proxies (CTR, VTR, attention) "
                "to infer brand impact."
            )

        if control == "No":
            risks.append(
                "No control group defined – this weakens the ability to prove incremental lift."
            )
            alternatives.append(
                "Set up a holdout geo / audience, even if small, for future flights."
            )

    elif objective == "Footfall / store visits":
        if offline_data == "Yes":
            primary = "Run a Footfall / Store Visit Study."
            methods.append("Location-based Footfall Uplift (exposed vs control visits)")
            details.append(
                "Measure exposed vs control visit rate using location signals and store "
                "POIs for the chosen market."
            )
        else:
            primary = "Use location reach & proximity as a proxy for footfall."
            methods.append("Reach within store catchments & visit propensity reporting")
            details.append(
                "Without reliable store visit data, report on reach within store catchments "
                "and visit propensity segments rather than strict incremental visits."
            )
            alternatives.append(
                "Explore enabling store visit data (via partners, beacons, Wi-Fi, or POS linkage) "
                "for future campaigns."
            )

    elif objective == "Sales / conversions":
        if offline_data == "Yes":
            primary = "Run a Sales Uplift / Matched Panel Study."
            methods.append("Sales Uplift using matched exposed vs control panel")
            details.append(
                "Use matched exposed vs control populations with sales or conversion data linked "
                "at customer, store or region level."
            )
        else:
            primary = (
                "Optimise towards performance KPIs (CPA / ROAS) rather than full Sales Uplift."
            )
            methods.append(
                "Performance optimisation using digital conversions and CPA / ROAS"
            )
            details.append(
                "Without transaction data, focus on digital conversions and cost-per-result, "
                "with directional modelling not strict uplift."
            )
            alternatives.append(
                "Work with the client to enable sales data sharing on future activity."
            )

    elif objective == "App installs / app usage":
        if offline_data == "Yes":
            primary = "Run an App Attribution & Incrementality Study."
            methods.append("App attribution + incrementality (MMP / SKAN / SDK data)")
            details.append(
                "Use MMP / SKAN / SDK data plus control design to measure incremental app installs "
                "or in-app actions."
            )
        else:
            primary = "Use standard app attribution with directional incrementality checks."
            methods.append("Standard app attribution with geo / audience trend checks")
            details.append(
                "Without full app analytics, attribute installs to media and use geo or "
                "audience-level trends as supporting evidence."
            )

    else:  # "Other / I'm not sure"
        primary = "Start with a simple effectiveness check and then escalate to a formal study."
        methods.append(
            "Basic effectiveness review (delivery, reach, frequency, CTR, VTR)"
        )
        details.append(
            "Clarify the true business outcome first. In the meantime, use basic media KPIs and "
            "simple exposed vs unexposed comparisons where feasible."
        )

    # --- Cross-cutting risk checks ---

    # Budget
    if budget_level == "Low":
        risks.append(
            "Budget is in the low band – sample sizes may be too small for a clean, "
            "statistically robust lift read."
        )
        alternatives.append(
            "Aggregate multiple similar campaigns into a pooled study, or downgrade from full "
            "lift to directional insights."
        )

    # Impressions
    if impressions_level == "Low":
        risks.append(
            "Planned impressions are low – this reduces the number of exposed users and events."
        )

    # Duration
    if duration in ["< 1 week", "1–2 weeks"]:
        risks.append(
            "Flight length is short – harder to accumulate enough exposed vs control data, "
            "especially for brand or sales outcomes."
        )
        alternatives.append(
            "Extend the flight to at least 2–3 weeks for brand / footfall / sales studies "
            "where possible."
        )

    # Market nuance – just a gentle note
    if market in ["India", "Other"]:
        details.append(
            "Check local data partners and privacy rules – measurement availability can vary "
            "by market."
        )

    # Bermuda Triangle: low spend + low impressions
    if budget_level == "Low" and impressions_level == "Low":
        risks.append(
            "Low spend AND low impressions – this is classic 'Bermuda Triangle' territory where "
            "results will likely be inconclusive."
        )

    return {
        "primary": primary,
        "details": details,
        "risks": risks,
        "alternatives": alternatives,
        "methods": methods,
    }


# -----------------------------
# UI
# -----------------------------
st.title("Blis Measurement Wizard")
st.caption(
    "Guided helper to choose the right measurement approach for each campaign. "
    "Designed for Sales (simple) and Analysts (detailed)."
)

st.markdown("---")

# Market selection
market = st.selectbox(
    "1. Which market is this campaign in?",
    list(MARKETS.keys()),
    index=2,  # default to India
)
market_info = MARKETS[market]
cur_symbol = market_info["currency_symbol"] or ""
cur_name = market_info["currency_name"]

st.info(
    f"Currency will be treated as **{cur_name}** "
    f"{'(' + cur_symbol + ')' if cur_symbol else ''} for budget bands."
)

# Objective
objective = st.radio(
    "2. What is the **primary campaign objective**?",
    [
        "Brand awareness / consideration",
        "Footfall / store visits",
        "Sales / conversions",
        "App installs / app usage",
        "Other / I'm not sure",
    ],
)

# IDs
ids = st.radio(
    "3. Do you have IDs / device identifiers / log-level data available for this campaign?",
    ["Yes", "No", "Not sure"],
)

# Budget
budget_labels = get_budget_band_labels(market_info)
budget_label = st.selectbox(
    f"4. Rough **media budget** in {cur_name} (choose the closest band)",
    budget_labels,
)
budget_level = get_budget_level(budget_label)

# Impressions
impressions_label = st.selectbox(
    "5. Rough **planned impressions** for this campaign?",
    [
        "< 100k",
        "100k–500k",
        "500k–1M",
        "1M+",
    ],
)
impressions_level = get_impression_level(impressions_label)

# Duration
duration = st.selectbox(
    "6. Expected **flight duration**?",
    [
        "< 1 week",
        "1–2 weeks",
        "2–4 weeks",
        "4+ weeks",
    ],
)

# Offline / sales / store data
offline_data = st.radio(
    "7. Do you have **store visit / sales / app analytics data** that we can link to media?",
    ["Yes", "No", "Not sure"],
)

# Control group
control = st.radio(
    "8. Can we design a **control group** (holdout geo / audience) for this activity?",
    ["Yes", "No", "Not sure"],
)

# Analyst mode toggle
show_analyst_view = st.checkbox(
    "Show analyst detail (method names, caveats)", value=False
)

st.markdown("---")

# -----------------------------
# Run engine on click
# -----------------------------
if st.button("Get measurement recommendation"):
    answers = {
        "market": market,
        "objective": objective,
        "ids": ids,
        "budget_level": budget_level,
        "impressions_level": impressions_level,
        "duration": duration,
        "offline_data": offline_data,
        "control": control,
    }

    # Feasibility status
    score = compute_feasibility_score(answers)
    status_text, status_type = map_score_to_status(score)

    if status_type == "success":
        st.success(f"Feasibility: {status_text}")
    elif status_type == "warning":
        st.warning(f"Feasibility: {status_text}")
    else:
        st.error(f"Feasibility: {status_text}")

    # Main recommendation
    rec = build_recommendation(answers)

    st.subheader("Recommended measurement approach")
    st.success(rec["primary"])

    # Analyst-only details
    if show_analyst_view and rec["methods"]:
        st.subheader("Suggested study types (for analysts)")
        for m in rec["methods"]:
            st.markdown(f"- {m}")

    if rec["details"]:
        st.subheader("How to frame this")
        for d in rec["details"]:
            st.markdown(f"- {d}")

    if rec["risks"]:
        st.subheader("Risks / limitations to flag")
        for r in rec["risks"]:
            st.markdown(f"- {r}")

    if rec["alternatives"]:
        st.subheader("Fallback options / backup plans")
        for a in rec["alternatives"]:
            st.markdown(f"- {a}")

    st.caption(
        "This is a v2 rules-based assistant. Analysts can fine-tune the rules over time "
        "by editing the compute_feasibility_score() and build_recommendation() functions."
    )
else:
    st.info("Fill in the answers above and click **Get measurement recommendation**.")
