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
    "EU": {"currency_symbol": "€", "currency_name": "EUR"},
    "AU": {"currency_symbol": "A$", "currency_name": "AUD"},
    "NZ": {"currency_symbol": "NZ$", "currency_name": "NZD"},
    "Asia": {"currency_symbol": "", "currency_name": "Local currency (Asia)"},
    "Benelux": {"currency_symbol": "€", "currency_name": "EUR"},
    "Italy": {"currency_symbol": "€", "currency_name": "EUR"},
    "India": {"currency_symbol": "₹", "currency_name": "INR"},
    "Other": {"currency_symbol": "", "currency_name": "Local currency"},
}


def get_budget_band_labels(market_info: dict):
    """Return human-readable budget bands using the market currency."""
    cur = market_info["currency_symbol"]
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
# Vendor hints by market & objective
# -----------------------------
def get_vendor_hint(market: str, objective: str) -> str:
    """
    Return a short text hint about likely partners / products by market.
    These are editable by analysts to match real Blis setups.
    """
    brand_vendors = {
        "US": "Brand lift via partners such as Lucid / Dynata.",
        "UK": "Brand lift via YouGov / On Device style partners.",
        "EU": "Brand lift via EU panel providers (Dynata / Cint, etc.).",
        "AU": "Brand lift via AU panels (Pureprofile / local partners).",
        "NZ": "Brand lift via AU/NZ panels (Pureprofile / local partners).",
        "Asia": "Brand lift via regional panels where available.",
        "Benelux": "Brand lift via EU/Benelux panel partners.",
        "Italy": "Brand lift via EU panel partners, subject to local privacy rules.",
        "India": "Brand lift via India panel partners where available.",
        "Other": "Brand lift via local panel partners where available.",
    }

    footfall_vendors = {
        "US": "Footfall via Blis location signals and US POI partners.",
        "UK": "Footfall via Blis location graph and UK POI data.",
        "EU": "Footfall via Blis EU location graph and POI partners.",
        "AU": "Footfall via AU mobile/location partners where available.",
        "NZ": "Footfall via NZ location partners where available.",
        "Asia": "Footfall via regional location graph; partner availability varies.",
        "Benelux": "Footfall via EU/Benelux location graph and POIs.",
        "Italy": "Footfall via EU graph; check local compliance.",
        "India": "Footfall via India location graph where active.",
        "Other": "Footfall via local location / POI partners where available.",
    }

    sales_vendors = {
        "US": "Sales uplift via US retail / card / loyalty data partners where live.",
        "UK": "Sales uplift via UK retail / loyalty / panel data partners.",
        "EU": "Sales uplift via EU retail or panel data partners where available.",
        "AU": "Sales uplift via AU retailer / panel partners where available.",
        "NZ": "Sales uplift via AU/NZ partners where available.",
        "Asia": "Sales uplift via local retail / e-com data where accessible.",
        "Benelux": "Sales uplift via EU panel/retail data partners.",
        "Italy": "Sales uplift via EU panel/retail data partners; check restrictions.",
        "India": "Sales uplift via India retail / e-commerce partners where available.",
        "Other": "Sales uplift via local retail / panel partners if available.",
    }

    app_vendors = {
        "US": "App measurement via MMPs (AppsFlyer / Adjust / Branch) and SKAN.",
        "UK": "App measurement via MMPs and UK app analytics setups.",
        "EU": "App measurement via MMPs with EU privacy-compliant setups.",
        "AU": "App measurement via MMPs for AU apps.",
        "NZ": "App measurement via MMPs for AU/NZ apps.",
        "Asia": "App measurement via regional MMP accounts.",
        "Benelux": "App measurement via EU MMP setups.",
        "Italy": "App measurement via EU MMP setups; ensure consent mechanisms.",
        "India": "App measurement via India-specific MMP integrations.",
        "Other": "App measurement via local MMP accounts.",
    }

    if "Brand awareness" in objective:
        return brand_vendors.get(market, "")
    if "Footfall" in objective:
        return footfall_vendors.get(market, "")
    if "Sales" in objective:
        return sales_vendors.get(market, "")
    if "App installs" in objective:
        return app_vendors.get(market, "")
    return ""


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

    budget_level = answers["budget_level"]
    impressions_level = answers["impressions_level"]
    duration = answers["duration"]
    objective = answers["objective"]
    ids = answers["ids"]
    offline_data = answers["offline_data"]
    expectation = answers["expectation"]
    other_media = answers["other_media"]
    creative = answers["creative"]

    if budget_level == "Low":
        score -= 1
    if impressions_level == "Low":
        score -= 1
    if duration in ["< 1 week", "1–2 weeks"]:
        score -= 1
    if objective == "Brand awareness / consideration" and ids == "No":
        score -= 1
    if objective in ["Footfall / store visits", "Sales / conversions"] and offline_data == "No":
        score -= 1
    # Expectation mismatch: client wants formal lift but inputs are weak
    if expectation == "Formal, statistically robust lift study" and (
        budget_level == "Low" or impressions_level == "Low"
    ):
        score -= 1
    # Heavy overlapping media makes isolation harder
    if other_media == "Yes":
        score -= 1
    # Weak creative makes all measurement noisier
    if creative == "Weak / poor fit / static banners only":
        score -= 1

    return score


def map_score_to_status(score: int) -> tuple[str, str]:
    """
    Map numeric score to a human label + streamlit message type.
    returns: (status_text, status_type) where status_type is
    one of 'success', 'warning', 'error'
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
    Rules-based engine.
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
    expectation = answers["expectation"]
    other_media = answers["other_media"]
    creative = answers["creative"]

    primary = ""
    details: list[str] = []
    risks: list[str] = []
    alternatives: list[str] = []
    methods: list[str] = []

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

        # Under-powered BLS theme
        if budget_level == "Low" or impressions_level == "Low":
            risks.append(
                "Brand Lift on low spend or low impressions is likely under-powered – treat any "
                "read as directional, not definitive proof."
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

    if budget_level == "Low":
        risks.append(
            "Budget is in the low band – sample sizes may be too small for a clean, "
            "statistically robust lift read."
        )
        alternatives.append(
            "Aggregate multiple similar campaigns into a pooled study, or downgrade from full "
            "lift to directional insights."
        )

    if impressions_level == "Low":
        risks.append(
            "Planned impressions are low – this reduces the number of exposed users and events."
        )

    if duration in ["< 1 week", "1–2 weeks"]:
        risks.append(
            "Flight length is short – harder to accumulate enough exposed vs control data, "
            "especially for brand or sales outcomes."
        )
        alternatives.append(
            "Extend the flight to at least 2–3 weeks for brand / footfall / sales studies "
            "where possible."
        )

    if market in ["India", "Asia", "Other"]:
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

    # Expectation vs reality mismatch
    if expectation == "Formal, statistically robust lift study" and (
        budget_level == "Low" or impressions_level == "Low" or duration in ["< 1 week", "1–2 weeks"]
    ):
        risks.append(
            "Client expects a formal, statistically robust lift read, but inputs look under-powered. "
            "Reframe expectations towards directional learning or adjust the plan."
        )
        alternatives.append(
            "Either increase scale (budget, impressions, duration) or reposition this as a "
            "directional / learning study instead of a definitive proof point."
        )

    # Other media noise
    if other_media == "Yes":
        risks.append(
            "There is heavy other media activity in the same markets/period – isolating the impact "
            "of this campaign alone will be harder."
        )
        alternatives.append(
            "Where possible, stagger campaigns, define clean test vs control regions, or use "
            "geo-level modelling that can account for overlapping spend."
        )

    # Creative quality
    if creative == "Weak / poor fit / static banners only":
        risks.append(
            "Creative is weak or poorly aligned – this reduces the chance of detecting any lift, "
            "even if measurement design is strong."
        )
        alternatives.append(
            "Consider a creative refresh or A/B test first, then rerun measurement on the stronger "
            "creative platform."
        )
    elif creative == "Average / not tested yet":
        details.append(
            "Creative has not been fully validated – treat results as a read on both media "
            "and creative performance."
        )

    # Attach vendor hint for analysts
    vendor_hint = get_vendor_hint(market, objective)
    if vendor_hint:
        methods.append(vendor_hint)

    return {
        "primary": primary,
        "details": details,
        "risks": risks,
        "alternatives": alternatives,
        "methods": methods,
    }


# -----------------------------
# Wizard state
# -----------------------------
st.title("Blis Measurement Wizard")
st.caption(
    "Internal Blis measurement concierge – designed with love for Sales & Analysts."
)
st.markdown("---")

TOTAL_STEPS = 12

if "step" not in st.session_state:
    st.session_state.step = 1

if "answers" not in st.session_state:
    st.session_state.answers = {
        "market": "India",
        "objective": "Brand awareness / consideration",
        "ids": "Not sure",
        "budget_label": "",
        "budget_level": "Medium",
        "impressions_label": "",
        "impressions_level": "Medium",
        "duration": "2–4 weeks",
        "offline_data": "Not sure",
        "control": "Not sure",
        "expectation": "Directional understanding / story is fine",
        "other_media": "Not sure",
        "creative": "Average / not tested yet",
        "show_analyst_view": False,
    }

answers = st.session_state.answers


def go_next():
    if st.session_state.step < TOTAL_STEPS:
        st.session_state.step += 1


def go_back():
    if st.session_state.step > 1:
        st.session_state.step -= 1


step = st.session_state.step
st.write(f"Step {step} of {TOTAL_STEPS}")

# -----------------------------
# Step-by-step questions
# -----------------------------
if step == 1:
    market = st.selectbox(
        "Which market is this campaign in?",
        list(MARKETS.keys()),
        index=list(MARKETS.keys()).index(answers["market"]),
    )
    answers["market"] = market
    market_info = MARKETS[market]
    cur_symbol = market_info["currency_symbol"] or ""
    cur_name = market_info["currency_name"]
    st.info(
        f"Currency will be treated as **{cur_name}** "
        f"{'(' + cur_symbol + ')' if cur_symbol else ''} for budget bands."
    )

elif step == 2:
    objective = st.radio(
        "What is the primary campaign objective?",
        [
            "Brand awareness / consideration",
            "Footfall / store visits",
            "Sales / conversions",
            "App installs / app usage",
            "Other / I'm not sure",
        ],
        index=[
            "Brand awareness / consideration",
            "Footfall / store visits",
            "Sales / conversions",
            "App installs / app usage",
            "Other / I'm not sure",
        ].index(answers["objective"]),
    )
    answers["objective"] = objective

elif step == 3:
    ids = st.radio(
        "Do you have IDs / device identifiers / log-level data available for this campaign?",
        ["Yes", "No", "Not sure"],
        index=["Yes", "No", "Not sure"].index(answers["ids"]),
    )
    answers["ids"] = ids

elif step == 4:
    market_info = MARKETS[answers["market"]]
    budget_labels = get_budget_band_labels(market_info)
    if answers["budget_label"] and answers["budget_label"] in budget_labels:
        default_index = budget_labels.index(answers["budget_label"])
    else:
        default_index = 1
    budget_label = st.selectbox(
        f"Rough media budget in {market_info['currency_name']} (choose the closest band)",
        budget_labels,
        index=default_index,
    )
    answers["budget_label"] = budget_label
    answers["budget_level"] = get_budget_level(budget_label)

elif step == 5:
    options = [
        "< 100k",
        "100k–500k",
        "500k–1M",
        "1M+",
    ]
    if answers["impressions_label"] and answers["impressions_label"] in options:
        default_index = options.index(answers["impressions_label"])
    else:
        default_index = 1
    impressions_label = st.selectbox(
        "Rough planned impressions for this campaign?",
        options,
        index=default_index,
    )
    answers["impressions_label"] = impressions_label
    answers["impressions_level"] = get_impression_level(impressions_label)

elif step == 6:
    options = [
        "< 1 week",
        "1–2 weeks",
        "2–4 weeks",
        "4+ weeks",
    ]
    default_index = options.index(answers["duration"]) if answers["duration"] in options else 2
    duration = st.selectbox(
        "Expected flight duration?",
        options,
        index=default_index,
    )
    answers["duration"] = duration

elif step == 7:
    offline_data = st.radio(
        "Do you have store visit / sales / app analytics data that we can link to media?",
        ["Yes", "No", "Not sure"],
        index=["Yes", "No", "Not sure"].index(answers["offline_data"]),
    )
    answers["offline_data"] = offline_data

elif step == 8:
    control = st.radio(
        "Can we design a control group (holdout geo / audience) for this activity?",
        ["Yes", "No", "Not sure"],
        index=["Yes", "No", "Not sure"].index(answers["control"]),
    )
    answers["control"] = control

elif step == 9:
    expectation = st.radio(
        "What is the client expecting from measurement?",
        [
            "Formal, statistically robust lift study",
            "Directional understanding / story is fine",
            "Not sure yet",
        ],
        index=[
            "Formal, statistically robust lift study",
            "Directional understanding / story is fine",
            "Not sure yet",
        ].index(answers["expectation"]),
    )
    answers["expectation"] = expectation

elif step == 10:
    other_media = st.radio(
        "Is there heavy other media activity in the same period/markets that we cannot cleanly control for (TV, OOH, big digital bursts)?",
        ["Yes", "No", "Not sure"],
        index=["Yes", "No", "Not sure"].index(answers["other_media"]),
    )
    answers["other_media"] = other_media

elif step == 11:
    creative = st.radio(
        "How would you rate the creative quality for this campaign?",
        [
            "Strong, tested creative aligned to the message",
            "Average / not tested yet",
            "Weak / poor fit / static banners only",
        ],
        index=[
            "Strong, tested creative aligned to the message",
            "Average / not tested yet",
            "Weak / poor fit / static banners only",
        ].index(answers["creative"]),
    )
    answers["creative"] = creative

elif step == 12:
    show_analyst_view = st.checkbox(
        "Show analyst detail (method names, vendors, caveats)",
        value=answers.get("show_analyst_view", False),
    )
    answers["show_analyst_view"] = show_analyst_view

    st.markdown("---")
    if st.button("Get measurement recommendation"):
        final_answers = {
            "market": answers["market"],
            "objective": answers["objective"],
            "ids": answers["ids"],
            "budget_level": answers["budget_level"],
            "impressions_level": answers["impressions_level"],
            "duration": answers["duration"],
            "offline_data": answers["offline_data"],
            "control": answers["control"],
            "expectation": answers["expectation"],
            "other_media": answers["other_media"],
            "creative": answers["creative"],
        }

        # Feasibility status
        score = compute_feasibility_score(final_answers)
        status_text, status_type = map_score_to_status(score)

        if status_type == "success":
            st.success(f"Feasibility: {status_text}")
        elif status_type == "warning":
            st.warning(f"Feasibility: {status_text}")
        else:
            st.error(f"Feasibility: {status_text}")

        # Main recommendation
        rec = build_recommendation(final_answers)

        st.subheader("Recommended measurement approach")
        st.success(rec["primary"])

        if show_analyst_view and rec["methods"]:
            st.subheader("Suggested study types & vendor notes (for analysts)")
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

        # -------- Email / deck summary --------
        st.markdown("---")
        st.subheader("Email / deck summary")

        summary_lines = [
            "Blis Measurement Recommendation",
            "-------------------------------",
            f"Market: {final_answers['market']}",
            f"Objective: {final_answers['objective']}",
            f"Client expectation: {final_answers['expectation']}",
            f"Creative quality: {final_answers['creative']}",
            f"Feasibility: {status_text}",
            "",
            "Recommended approach:",
            f"- {rec['primary']}",
        ]

        if rec["methods"]:
            summary_lines.append("")
            summary_lines.append("Suggested study types / vendor notes:")
            for m in rec["methods"]:
                summary_lines.append(f"- {m}")

        if rec["risks"]:
            summary_lines.append("")
            summary_lines.append("Key risks / limitations:")
            for r in rec["risks"]:
                summary_lines.append(f"- {r}")

        if rec["alternatives"]:
            summary_lines.append("")
            summary_lines.append("Fallback options / backup plans:")
            for a in rec["alternatives"]:
                summary_lines.append(f"- {a}")

        summary_text = "\n".join(summary_lines)

        st.code(summary_text, language="text")
        st.download_button(
            "Download summary as .txt",
            data=summary_text,
            file_name="blis_measurement_recommendation.txt",
        )

        st.caption(
            "This is a v5 rules-based assistant. Analysts can fine-tune the rules over time "
            "by editing the compute_feasibility_score(), get_vendor_hint(), and "
            "build_recommendation() functions."
        )

# -----------------------------
# Navigation controls
# -----------------------------
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if step > 1:
        st.button("← Back", on_click=go_back)
with col2:
    if step < TOTAL_STEPS:
        st.button("Next →", on_click=go_next)
