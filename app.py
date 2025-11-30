import streamlit as st

# -----------------------------
# Basic page config & styling
# -----------------------------
st.set_page_config(page_title="Blis Measurement Wizard", layout="centered")

# Bump base font size and make question headings bigger
st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-size: 16px;
    }
    .question-heading {
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        low = "Low (small test budget, may be under ~30k)"
        med = "Medium (around 30k–100k)"
        high = "High (100k+)"
    else:
        low = f"Low ({cur}0–{cur}30k, may be under threshold)"
        med = f"Medium ({cur}30k–{cur}100k)"
        high = f"High ({cur}100k+)"
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
# Vendor-ish hints by market & objective (generic)
# -----------------------------
def get_vendor_hint(market: str, objective: str) -> str:
    """
    Return a short text hint about likely partner / product shape by market.
    Only reflects what’s implied in the stickies (panel vs location vs sales vs app vendors).
    """
    if "Brand awareness" in objective:
        return {
            "US": "Brand lift via established US panel/brand study partners.",
            "UK": "Brand lift via UK panel/brand study partners.",
            "EU": "Brand lift via EU panel providers.",
            "AU": "Brand lift via AU/NZ panel providers.",
            "NZ": "Brand lift via AU/NZ panel providers.",
            "Asia": "Brand lift via regional panel partners where available.",
            "Benelux": "Brand lift via EU/Benelux panel partners.",
            "Italy": "Brand lift via EU/IT panel partners, respecting local privacy.",
            "India": "Brand lift via India panel partners where active.",
            "Other": "Brand lift via local/regional panel partners where available.",
        }.get(market, "")
    if "Footfall" in objective:
        return {
            "US": "Footfall using Blis location graph and US POI/visit partners.",
            "UK": "Footfall using Blis UK location graph and POI data.",
            "EU": "Footfall using Blis EU location graph and retail POIs.",
            "AU": "Footfall using AU/NZ location partners where available.",
            "NZ": "Footfall using AU/NZ location partners where available.",
            "Asia": "Footfall using regional location graph where coverage allows.",
            "Benelux": "Footfall using EU/Benelux location graph and POIs.",
            "Italy": "Footfall using EU/IT graph; check store coverage and compliance.",
            "India": "Footfall using India location graph where active.",
            "Other": "Footfall via local/regional location and POI partners.",
        }.get(market, "")
    if "Sales / conversions" in objective:
        return {
            "US": "Sales uplift using available retail/e-comm/panel data sources.",
            "UK": "Sales uplift using UK retail/panel/loyalty data where enabled.",
            "EU": "Sales uplift using EU retail/panel data where enabled.",
            "AU": "Sales uplift using AU retailer/panel data where available.",
            "NZ": "Sales uplift using AU/NZ retail data where available.",
            "Asia": "Sales uplift using local e-commerce/retail data where clients provide it.",
            "Benelux": "Sales uplift using EU/Benelux retail or panel data where available.",
            "Italy": "Sales uplift using EU/IT retail/panel data; check legal constraints.",
            "India": "Sales uplift using India retail/e-commerce data where enabled.",
            "Other": "Sales uplift using local retail/panel data where available.",
        }.get(market, "")
    if "App installs" in objective:
        return {
            "US": "App uplift measurement via app analytics/MMP-style partners.",
            "UK": "App uplift measurement via UK app analytics/MMP setups.",
            "EU": "App uplift measurement via EU app analytics/MMP setups.",
            "AU": "App uplift measurement via AU/NZ app analytics setups.",
            "NZ": "App uplift measurement via AU/NZ app analytics setups.",
            "Asia": "App uplift measurement via regional app analytics setups.",
            "Benelux": "App uplift measurement via EU app analytics setups.",
            "Italy": "App uplift measurement via EU/IT app analytics setups.",
            "India": "App uplift measurement via India app analytics/MMP setups.",
            "Other": "App uplift measurement via local app analytics/MMP setups.",
        }.get(market, "")
    return ""


# -----------------------------
# Feasibility scoring (based on stickies)
# -----------------------------
def compute_feasibility_score(answers: dict) -> int:
    """
    Start from 3 and subtract points for risk factors from the sticky notes.
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
    niche = answers["niche_audience"]

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
    if expectation == "Formal, statistically robust lift study" and (
        budget_level == "Low" or impressions_level == "Low"
    ):
        score -= 1
    if other_media == "Yes":
        score -= 1
    if creative == "Weak / poor fit / static banners only":
        score -= 1
    if objective == "Brand awareness / consideration" and niche == "Yes":
        # B2B/niche audiences sticky
        score -= 1

    return score


def map_score_to_status(score: int) -> tuple[str, str]:
    """Map numeric score to a label & Streamlit message type."""
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
    Rules-based engine reflecting the sticky notes.
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
    omnichannel = answers["omnichannel"]
    niche = answers["niche_audience"]
    bls_timing = answers["bls_timing"]

    primary = ""
    details: list[str] = []
    risks: list[str] = []
    alternatives: list[str] = []
    methods: list[str] = []

    # --- Objective-specific recommendations & minimums from stickies ---

    if objective == "Brand awareness / consideration":
        # If we cannot rely on IDs for the whole campaign or omnichannel is messy -> SHG
        if ids != "Yes" or omnichannel == "Yes":
            primary = "Run an SHG-based Brand Lift / custom uplift study (min ~100k media spend)."
            methods.append("BLS SHG (minimum ~100k media spend).")
            methods.append("If SHG is not possible, use ODR-style survey (minimum ~40k).")
            details.append(
                "Channels without IDs (audio, OOH, CTV, off-platform) and omnichannel activity "
                "require SHG-type brand lift or an ODR survey rather than pure ID-based BLS."
            )
        else:
            primary = "Run an ID-based Brand Lift Study (min ~30k media spend)."
            methods.append("BLS ID (minimum ~30k media spend).")
            methods.append("Optionally, BLS SHG (minimum ~100k) for broader omnichannel coverage.")
            methods.append("ODR survey (minimum ~40k) as an alternative panel-based approach.")
            details.append(
                "Use exposed vs control Brand Lift with IDs where available. "
                "If additional channels lack IDs, consider SHG to capture them."
            )

        # Control group
        if control == "No":
            risks.append(
                "No control group defined – this weakens the ability to prove incremental lift."
            )
            alternatives.append(
                "Set up a holdout geo/audience, even if small, for future flights."
            )

        # Under-powered BLS & 30k example
        if budget_level == "Low":
            risks.append(
                "Running a BLS under ~30k spend can produce too small a sample for valid results. "
                "Example from the sticky: £8 CPM on a £30k budget ≈ 240,000 impressions → "
                "80,000 unique reach at frequency 3 → 800 clicks at 1% CTR → "
                "80 completes at 10% completion – too small a sample."
            )
            alternatives.append(
                "Either increase spend beyond ~30k or treat any Brand Lift read as small-sample "
                "and directional."
            )

        # BLS timing
        if bls_timing == "After/close to the end of campaign":
            risks.append(
                "Running a BLS after/close to the end of a campaign makes it hard to get a "
                "representative sample; subconscious recognition even 48 hours after exposure "
                "can be limited."
            )

        # Niche audience / B2B
        if niche == "Yes":
            risks.append(
                "B2B/niche audience: likelihood of reaching enough respondents with BLS is very low."
            )
            alternatives.append(
                "Consider broader proxy audiences or alternative methods (qual, desk research, "
                "panel-based surveys not tied only to exposure)."
            )

        # Respondent experience
        risks.append(
            "Respondent experience: avoid too many answer options, overly long questions, or "
            "excessive survey length – these reduce completion and data quality."
        )

    elif objective == "Footfall / store visits":
        # Footfall uplift, Blis or Unacast – SHG 100k min, ID 30k min
        if offline_data == "Yes":
            if ids == "Yes":
                primary = "Run an ID-based Footfall Uplift study (min ~30k media spend)."
                methods.append("Footfall uplift (ID-based) – minimum ~30k.")
                methods.append("Footfall uplift via SHG (minimum ~100k) for omnichannel/no-ID media.")
            else:
                primary = "Run an SHG-based Footfall Uplift study (min ~100k media spend)."
                methods.append("Footfall uplift (SHG) – minimum ~100k.")
            details.append(
                "Use Blis/partner location data to compare exposed vs control store visits."
            )
        else:
            primary = "Use location reach & proximity as a proxy for footfall (no visit data)."
            methods.append("Reach within store catchments & visit propensity reporting.")
            details.append(
                "Without reliable store visit data, report on reach within store catchments "
                "and density of impressions around stores instead of strict uplift."
            )
            alternatives.append(
                "Enable store visit data (via partners, beacons, Wi-Fi, or POS linkage) "
                "for future campaigns."
            )

    elif objective == "Sales / conversions":
        # Mastercard by merchant / Circana by product with min spends
        if offline_data == "Yes":
            primary = "Run a Sales Uplift study using merchant/product-level data."
            methods.append("Mastercard by merchant (minimum ~120k media spend).")
            methods.append("Circana by product (minimum ~100k media spend).")
            details.append(
                "Use matched exposed vs control at merchant/product level with panel or "
                "transaction data, respecting the minimum spends."
            )
        else:
            primary = (
                "Optimise towards performance KPIs (CPA/ROAS); full sales uplift not feasible "
                "without transaction data."
            )
            details.append(
                "Without sales data (Mastercard/Circana or similar), you can still optimise "
                "towards digital conversions but not run a formal sales uplift."
            )
            alternatives.append(
                "Work with the client to enable sales data sharing or partner connections "
                "for future uplift work."
            )

    elif objective == "App installs / app usage":
        # VMO2 / Vodafone – O2 App uplift (120k min)
        if offline_data == "Yes":
            primary = "Run an App Uplift study for key telco/app partners (min ~120k media spend)."
            methods.append("O2/VMO2-style app uplift (minimum ~120k media spend).")
            details.append(
                "Use app analytics to compare exposed vs control app usage/installs, "
                "respecting partner minimums."
            )
        else:
            primary = "Use standard app analytics and attribution with directional uplift checks."
            methods.append("Standard app attribution with simple uplift checks by geo/audience.")
            details.append(
                "Without dedicated app uplift partners, attribute installs to media and use "
                "trend differences as directional evidence."
            )

    else:  # "Other / I'm not sure"
        primary = "Run an SHG/custom uplift approach where possible (min ~100k media spend)."
        methods.append("Other/custom uplift via SHG (minimum ~100k).")
        details.append(
            "For bespoke outcomes, use SHG/custom uplift as long as minimum volume is met; "
            "otherwise fall back to directional KPIs."
        )

    # --- Cross-cutting risk checks / caveats ---

    # Budget/30k threshold
    if budget_level == "Low":
        risks.append(
            "Budget/spend may be below the ~30k threshold mentioned in the guidelines – this "
            "can limit sample size and statistical power for any formal study."
        )

    # SHG 100k + Bermuda triangle
    if budget_level == "Low" and impressions_level == "Low":
        risks.append(
            "Low spend AND low impressions – this is the 'Bermuda Triangle' where results "
            "often get lost and studies struggle to find lift."
        )
        alternatives.append(
            "Either increase scale (budget/impressions) or avoid promising a formal uplift "
            "study; treat any read as exploratory."
        )

    if impressions_level == "Low":
        risks.append(
            "Number of impressions and density of impressions may be too low for robust "
            "learning – unique reach and per-postcode distribution will be light."
        )

    # Duration / reach / distribution row
    if duration in ["< 1 week", "1–2 weeks"]:
        risks.append(
            "Duration is short – limited time to build reach and frequency, especially if "
            "there are bursts of activity."
        )
    if niche == "Yes":
        risks.append(
            "Niche audience (e.g., ultra high net worth, B2B decision makers) – "
            "budget vs reach trade-off is tough, and results may be volatile."
        )

    # Other media noise
    if other_media == "Yes":
        risks.append(
            "Heavy other media (TV, OOH, big digital bursts) in the same period/markets makes "
            "it harder to isolate this campaign's impact."
        )
        alternatives.append(
            "Where possible, stagger campaigns, define clean test vs control regions, or "
            "apply geo-level designs that consider other media."
        )

    # Creative quality
    if creative == "Weak / poor fit / static banners only":
        risks.append(
            "Creative is weak or poorly aligned – even a perfect measurement design may fail "
            "to show lift if the creative does not drive behaviour."
        )
        alternatives.append(
            "Consider improving or testing creative first, then rerunning measurement on a "
            "stronger platform."
        )
    elif creative == "Average / not tested yet":
        details.append(
            "Creative has not been fully tested – treat results as a read on both media and "
            "creative effectiveness."
        )

    # Market caveat
    if market in ["India", "Asia", "Other"]:
        risks.append(
            "Market data coverage and partner availability can vary – check in-market teams "
            "before promising specific methodologies."
        )

    # Attach vendor-ish hint
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

TOTAL_STEPS = 14

if "step" not in st.session_state:
    st.session_state.step = 1

if "answers" not in st.session_state:
    st.session_state.answers = {
        "market": "UK",
        "objective": "Brand awareness / consideration",
        "ids": "Not sure",
        "omnichannel": "Not sure",
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
        "niche_audience": "No",
        "bls_timing": "During main body of campaign",
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
    st.markdown(
        '<div class="question-heading">Which market is this campaign in?</div>',
        unsafe_allow_html=True,
    )
    market = st.selectbox(
        "",
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
    st.markdown(
        '<div class="question-heading">Do we have IDs for this activity?</div>',
        unsafe_allow_html=True,
    )
    st.write(
        "IDs typically exist for **in-app display / on-platform** activity. "
        "Audio, OOH, CTV and off-platform channels often do **not** have IDs."
    )
    ids = st.radio(
        "",
        ["Yes", "No", "Not sure"],
        index=["Yes", "No", "Not sure"].index(answers["ids"]),
    )
    answers["ids"] = ids

elif step == 3:
    st.markdown(
        '<div class="question-heading">Is this an omnichannel campaign?</div>',
        unsafe_allow_html=True,
    )

    options = [
        "Yes – includes channels where we do NOT have IDs (audio, OOH, CTV, off-platform)",
        "No – all key activity is ID-based/in-app display",
        "Not sure",
    ]

    stored = answers["omnichannel"]
    if stored == "Yes":
        default_index = 0
    elif stored == "No":
        default_index = 1
    else:
        default_index = 2

    choice = st.radio("", options, index=default_index)

    if choice.startswith("Yes"):
        answers["omnichannel"] = "Yes"
    elif choice.startswith("No"):
        answers["omnichannel"] = "No"
    else:
        answers["omnichannel"] = "Not sure"

elif step == 4:
    st.markdown(
        '<div class="question-heading">What do we want to measure?</div>',
        unsafe_allow_html=True,
    )
    objective = st.radio(
        "",
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

elif step == 5:
    st.markdown(
        '<div class="question-heading">Rough media budget for this campaign?</div>',
        unsafe_allow_html=True,
    )
    market_info = MARKETS[answers["market"]]
    budget_labels = get_budget_band_labels(market_info)
    if answers["budget_label"] and answers["budget_label"] in budget_labels:
        default_index = budget_labels.index(answers["budget_label"])
    else:
        default_index = 1
    budget_label = st.selectbox(
        f"(in {market_info['currency_name']}, choose the closest band)",
        budget_labels,
        index=default_index,
    )
    answers["budget_label"] = budget_label
    answers["budget_level"] = get_budget_level(budget_label)

elif step == 6:
    st.markdown(
        '<div class="question-heading">Rough planned impressions for this campaign?</div>',
        unsafe_allow_html=True,
    )
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
        "",
        options,
        index=default_index,
    )
    answers["impressions_label"] = impressions_label
    answers["impressions_level"] = get_impression_level(impressions_label)

elif step == 7:
    st.markdown(
        '<div class="question-heading">Expected length of campaign?</div>',
        unsafe_allow_html=True,
    )
    options = [
        "< 1 week",
        "1–2 weeks",
        "2–4 weeks",
        "4+ weeks",
    ]
    default_index = options.index(answers["duration"]) if answers["duration"] in options else 2
    duration = st.selectbox(
        "",
        options,
        index=default_index,
    )
    answers["duration"] = duration
    st.caption("Includes bursts of activity if the campaign is not continuous.")

elif step == 8:
    st.markdown(
        '<div class="question-heading">Do you have store visit / sales / app analytics data that we can link to media?</div>',
        unsafe_allow_html=True,
    )
    offline_data = st.radio(
        "",
        ["Yes", "No", "Not sure"],
        index=["Yes", "No", "Not sure"].index(answers["offline_data"]),
    )
    answers["offline_data"] = offline_data

elif step == 9:
    st.markdown(
        '<div class="question-heading">Is this a niche / B2B audience?</div>',
        unsafe_allow_html=True,
    )
    niche = st.radio(
        "",
        [
            "No – relatively broad consumer audience",
            "Yes – niche/B2B (e.g. ultra high net worth, B2B decision makers)",
        ],
        index=0 if answers["niche_audience"] == "No" else 1,
    )
    answers["niche_audience"] = "Yes" if niche.startswith("Yes") else "No"

elif step == 10:
    st.markdown(
        '<div class="question-heading">Is there heavy other media activity in the same period/markets that we cannot cleanly control for?</div>',
        unsafe_allow_html=True,
    )
    other_media = st.radio(
        "",
        ["Yes", "No", "Not sure"],
        index=["Yes", "No", "Not sure"].index(answers["other_media"]),
    )
    answers["other_media"] = other_media
    st.caption("Think TV, OOH, big digital bursts from other partners, etc.")

elif step == 11:
    st.markdown(
        '<div class="question-heading">How would you rate the creative quality for this campaign?</div>',
        unsafe_allow_html=True,
    )
    creative = st.radio(
        "",
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
    # Only strictly matters for Brand / BLS, but we’ll ask once
    st.markdown(
        '<div class="question-heading">If you’re considering Brand Lift, when will the survey run?</div>',
        unsafe_allow_html=True,
    )
    bls_timing = st.radio(
        "",
        [
            "During main body of campaign (good spread of exposure)",
            "After/close to the end of campaign",
            "Not planning Brand Lift / not sure",
        ],
        index=[
            "During main body of campaign (good spread of exposure)",
            "After/close to the end of campaign",
            "Not planning Brand Lift / not sure",
        ].index(answers["bls_timing"]),
    )
    answers["bls_timing"] = bls_timing

elif step == 13:
    st.markdown(
        '<div class="question-heading">What is the client expecting from measurement?</div>',
        unsafe_allow_html=True,
    )
    expectation = st.radio(
        "",
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

elif step == 14:
    st.markdown(
        '<div class="question-heading">Do you want analyst detail (methods, vendor notes, caveats) in the output?</div>',
        unsafe_allow_html=True,
    )
    show_analyst_view = st.checkbox(
        "",
        value=answers.get("show_analyst_view", False),
    )
    answers["show_analyst_view"] = show_analyst_view

    st.markdown("---")
    if st.button("Get measurement recommendation"):
        final_answers = {
            "market": answers["market"],
            "objective": answers["objective"],
            "ids": answers["ids"],
            "omnichannel": answers["omnichannel"],
            "budget_level": answers["budget_level"],
            "impressions_level": answers["impressions_level"],
            "duration": answers["duration"],
            "offline_data": answers["offline_data"],
            "control": answers["control"],
            "expectation": answers["expectation"],
            "other_media": answers["other_media"],
            "creative": answers["creative"],
            "niche_audience": answers["niche_audience"],
            "bls_timing": answers["bls_timing"],
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
            f"Niche audience: {final_answers['niche_audience']}",
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
            "Analysts can refine rules by editing compute_feasibility_score(), "
            "get_vendor_hint(), and build_recommendation()."
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
