import streamlit as st

# -----------------------------
# Basic page config & styling
# -----------------------------
st.set_page_config(page_title="Blis Measurement Wizard", layout="centered")

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
    .subtle-label {
        font-size: 13px;
        color: #666666;
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
    """
    Budget bands aligned to sticky-note thresholds:
    - 30k is the key minimum threshold for most analyses
    - 100k+ is where SHG and custom uplifts start to be viable
    """
    cur = market_info["currency_symbol"]
    if cur == "":
        low = "Low (may be under 30k – below core measurement thresholds)"
        med = "Medium (around 30k–100k)"
        high = "High (100k+)"
    else:
        low = f"Low ({cur}0–{cur}30k – may be under 30k threshold)"
        med = f"Medium ({cur}30k–{cur}100k)"
        high = f"High ({cur}100k+)"
    return [low, med, high]


def get_budget_level(budget_label: str) -> str:
    label = budget_label.lower()
    if "low" in label:
        return "Low"
    if "high" in label:
        return "High"
    return "Medium"


def get_impression_level(imp_label: str) -> str:
    """
    We keep a simple mapping so that we can talk about:
    - density of impressions
    - number of impressions
    and the 'Bermuda Triangle' when both are low.
    """
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
    Score starts at 3 (solid). Each limiting factor from the sticky notes
    reduces the score. We do not invent new thresholds – we only apply
    what is explicitly noted:
    - Budget / spend threshold
    - Delivery, density and number of impressions
    - Duration
    - IDs / methodology fit
    - Offline data availability
    - Niche audiences
    - Other media noise
    - Creative quality
    - Expectation of formal vs directional read
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
    omnichannel = answers["omnichannel"]
    bls_timing = answers["bls_timing"]

    # Budget / spend threshold (minimum 30k to run most analyses properly)
    if budget_level == "Low":
        score -= 1

    # Density / number of impressions
    if impressions_level == "Low":
        score -= 1

    # Duration (includes bursts of activity)
    if duration in ["< 1 week", "1–2 weeks"]:
        score -= 1

    # Brand lift without IDs is harder to run as an ID-based BLS
    if objective == "Brand awareness / consideration" and ids == "No":
        score -= 1

    # Footfall / Sales / App uplift require some kind of offline or app data
    if objective in ["Footfall / store visits", "Sales / conversions", "App installs / app usage"] and offline_data == "No":
        score -= 1

    # If the client expects a formal, statistically robust lift study,
    # low budget or low impressions are material risks.
    if expectation == "Formal, statistically robust lift study" and (
        budget_level == "Low" or impressions_level == "Low"
    ):
        score -= 1

    # Heavy other media activity makes isolation harder
    if other_media == "Yes":
        score -= 1

    # Weak creative limits any chance of measurable lift
    if creative == "Weak / poor fit / static banners only":
        score -= 1

    # Niche / B2B audiences are flagged in the stickies as low-feasibility for BLS
    if objective == "Brand awareness / consideration" and niche == "Yes":
        score -= 1

    # Running BLS after / close to the end of the campaign is a known issue
    if objective == "Brand awareness / consideration" and bls_timing == "After/close to the end of campaign":
        score -= 1

    # Omnichannel including non-ID media adds complexity for ID-based reads
    if omnichannel == "Yes" and objective == "Brand awareness / consideration":
        score -= 1

    return max(score, 0)


def map_score_to_status(score: int) -> tuple[str, str]:
    """
    We keep this simple and qualitative, as the stickies never define
    exact numeric quality tiers – they just talk about where results
    'get lost' versus where they are more robust.
    """
    if score >= 3:
        return "Strong measurement feasible", "success"
    if score == 2:
        return "Feasible but with clear caveats", "warning"
    if score == 1:
        return "Borderline – treat as directional only", "warning"
    return "Not recommended as a formal study – directional at best", "error"


# -----------------------------
# Recommendation logic
# -----------------------------
def build_recommendation(answers: dict) -> dict:
    """
    Build the recommendation using only the structures, thresholds and
    caveats present on the sticky notes.
    """
    objective = answers["objective"]
    ids = answers["ids"]
    budget_level = answers["budget_level"]
    impressions_level = answers["impressions_level"]
    duration = answers["duration"]
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

    # -------------------------
    # Core recommendation by objective
    # -------------------------
    if objective == "Brand awareness / consideration":
        # Methodology: Do we have IDs or not? If not, it has to be SHG.
        if ids != "Yes" or omnichannel == "Yes":
            primary = "Run a Brand Lift via SHG / custom uplift (minimum 100k media spend)."
            methods.append("Brand Lift via SHG (minimum 100k).")
            methods.append("If SHG is not possible, consider an ODR survey (minimum 40k).")
            details.append(
                "Because IDs are missing on key channels or the campaign is omnichannel, "
                "SHG-style Brand Lift or an ODR survey is more suitable than pure ID-based BLS."
            )
        else:
            primary = "Run an ID-based Brand Lift Study (minimum 30k media spend)."
            methods.append("Brand Lift Study (ID-based, minimum 30k).")
            methods.append("If additional non-ID channels are important, consider SHG Brand Lift (minimum 100k).")
            methods.append("ODR survey (minimum 40k) can be used where panel-based brand work is preferred.")
            details.append(
                "Where IDs are present, use exposed vs control Brand Lift. "
                "If campaign mix shifts into non-ID channels, SHG can be layered in."
            )

        # Common mistakes / reasons – all directly from the stickies.
        if budget_level == "Low":
            risks.append(
                "Running a BLS under 30k can result in too small a sample and invalid results. "
                "Example CPM of £8 on a £30k budget ≈ 240,000 impressions → "
                "240,000 / frequency of 3 ≈ 80,000 unique reach → 1% CTR gives 800 clicks → "
                "10% completion rate gives 80 completes, which is too small a sample."
            )
            alternatives.append(
                "Increase spend to at least 30k for ID-based BLS, or shift to SHG/ODR with a higher budget."
            )

        if bls_timing == "After/close to the end of campaign":
            risks.append(
                "Running BLS after or very close to the end of a campaign limits the chance of getting "
                "a representative sample and reduces subconscious recognition even 48 hours after exposure."
            )

        if niche == "Yes":
            risks.append(
                "B2B / niche audiences: likelihood of reaching them with BLS at scale is very low."
            )
            alternatives.append(
                "Consider broader proxy audiences, alternative research (qual, desk), or use Brand Lift only "
                "as a directional read."
            )

        # Respondent experience / survey design
        risks.append(
            "Respondent experience: avoid too many answer options, overly long questions or character-heavy text. "
            "These reduce completion rates and data quality."
        )

    elif objective == "Footfall / store visits":
        if offline_data == "Yes":
            if ids == "Yes":
                primary = "Run an ID-based Footfall Uplift study (minimum 30k media spend)."
                methods.append("Footfall uplift (ID-based, minimum 30k).")
                methods.append("If IDs are limited, consider SHG-based footfall uplift (minimum 100k).")
            else:
                primary = "Run an SHG-based Footfall Uplift study (minimum 100k media spend)."
                methods.append("Footfall uplift via SHG (minimum 100k).")
            details.append(
                "Use location data (Blis or partners) to compare exposed vs control store visits."
            )
        else:
            primary = "Report on proximity and reach around stores; a formal footfall uplift study is not possible."
            methods.append("Report on reach, delivery and density of impressions around store postcodes.")
            details.append(
                "Without store-visit or equivalent offline data, focus on distribution of impressions and "
                "reach in store catchments rather than formal uplift."
            )
            alternatives.append(
                "Work with the client to enable store-visit or equivalent data for future uplift work."
            )

    elif objective == "Sales / conversions":
        if offline_data == "Yes":
            primary = "Run a Sales Uplift study using merchant/product-level data."
            methods.append("Mastercard uplift by merchant (minimum 120k).")
            methods.append("Circana uplift by product (minimum 100k).")
            details.append(
                "Use exposed vs control matched at merchant or product level, following the minimum spends."
            )
        else:
            primary = (
                "Optimise to digital performance KPIs (e.g. conversions, ROAS). "
                "A formal sales uplift read is not possible without sales or transaction data."
            )
            details.append(
                "Without sales data, we can still optimise but cannot run a proper sales uplift study."
            )
            alternatives.append(
                "Enable Mastercard / Circana or client sales data integrations for future campaigns."
            )

    elif objective == "App installs / app usage":
        if offline_data == "Yes":
            primary = "Run an App Uplift study via eligible partners (minimum 120k media spend)."
            methods.append("O2 / VMO2-style App Uplift (minimum 120k).")
            details.append(
                "Use app analytics to compare exposed vs control app usage or installs, respecting partner minimums."
            )
        else:
            primary = "Use standard attribution and app analytics with directional uplift reads only."
            methods.append("App attribution plus directional checks by geo or audience.")
            details.append(
                "Without a dedicated app uplift framework, attribute installs to media and treat uplift as directional."
            )

    else:
        primary = "Use a custom uplift study via SHG where budgets allow (minimum 100k)."
        methods.append("Custom uplift via SHG (minimum 100k).")
        details.append(
            "For bespoke outcomes, use SHG-based custom uplift where minimum budgets are met; "
            "otherwise, rely on campaign KPIs directionally."
        )

    # -------------------------
    # Cross-cutting caveats & limiting factors
    # -------------------------

    # Budget / spend threshold
    if budget_level == "Low":
        risks.append(
            "Budget / spend threshold: below roughly 30k, most structured analyses struggle to achieve stable sample sizes."
        )

    # Bermuda Triangle – where results get lost
    if budget_level == "Low" and impressions_level == "Low":
        risks.append(
            "This sits in the 'Bermuda Triangle' – low budget and low number of impressions. "
            "Results are likely to get lost in noise."
        )
        alternatives.append(
            "Increase budget and impressions, tighten targeting, or avoid positioning this as a formal uplift study."
        )

    # Density / distribution of impressions per postcode
    if impressions_level == "Low":
        risks.append(
            "Number and density of impressions are limited. Distribution across postcodes may be patchy, "
            "reducing representativeness."
        )

    # Duration / bursts of activity
    if duration in ["< 1 week", "1–2 weeks"]:
        risks.append(
            "Duration is short (even allowing for bursts of activity). It may not allow enough time to build reach and frequency."
        )

    # Budget vs reach mismatches (too broad an audience vs budget)
    if budget_level == "Low" and impressions_level in ["Medium", "High"]:
        risks.append(
            "Budget vs reach tension: audience may be too broad relative to spend, which can thin out impressions "
            "and weaken effectiveness (e.g. broad sporty audience for a specialist brand)."
        )

    if niche == "Yes":
        risks.append(
            "Things that can limit effectiveness: niche or ultra high value audiences are harder to reach consistently "
            "and can struggle to hit the minimum sample requirements."
        )

    # Other media
    if other_media == "Yes":
        risks.append(
            "Other media running in the same markets and period will make it harder to isolate this activity's impact."
        )
        alternatives.append(
            "Where possible, separate test vs control geographies or time periods to reduce contamination from other media."
        )

    # Creative quality
    if creative == "Weak / poor fit / static banners only":
        risks.append(
            "Creative quality: weak, static or poorly aligned creative can limit the chance of seeing any measurable lift, "
            "regardless of methodology."
        )
        alternatives.append(
            "Strengthen creative (messaging, formats, assets) and treat any current read as directional only."
        )
    elif creative == "Average / not tested yet":
        details.append(
            "Creative has not been fully tested – interpret results as a read on both media and creative effectiveness."
        )

    # Market-level note (without assuming specifics)
    risks.append(
        "Market you are advertising in can affect feasibility (panel coverage, data availability, partner access). "
        "Check local constraints before committing to specific vendors."
    )

    # Control / holdout – always a consideration, even if not explicitly captured
    risks.append(
        "Ensure there is a clear control or holdout group. Without a proper control, results become directional rather than definitive."
    )

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
st.caption("Internal Blis measurement concierge – designed with love for Sales & Analysts.")
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
        "Channels where we typically have IDs include in-app display / on-platform activity. "
        "Channels where we usually do not have IDs include audio, OOH, CTV and off-platform."
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
        "Yes – includes channels where we do not have IDs (audio, OOH, CTV, off-platform)",
        "No – all key activity is ID-based / in-app display",
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
    st.caption("The 30k mark is the key threshold for many uplift and Brand Lift analyses.")

elif step == 6:
    st.markdown(
        '<div class="question-heading">Rough planned impressions for this campaign?</div>',
        unsafe_allow_html=True,
    )
    options = ["< 100k", "100k–500k", "500k–1M", "1M+"]
    if answers["impressions_label"] and answers["impressions_label"] in options:
        default_index = options.index(answers["impressions_label"])
    else:
        default_index = 1
    impressions_label = st.selectbox("", options, index=default_index)
    answers["impressions_label"] = impressions_label
    answers["impressions_level"] = get_impression_level(impressions_label)
    st.caption("Impressions link to density, delivery and the ability to build enough unique reach.")

elif step == 7:
    st.markdown(
        '<div class="question-heading">Expected length of campaign?</div>',
        unsafe_allow_html=True,
    )
    options = ["< 1 week", "1–2 weeks", "2–4 weeks", "4+ weeks"]
    default_index = options.index(answers["duration"]) if answers["duration"] in options else 2
    duration = st.selectbox("", options, index=default_index)
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
            "Yes – niche/B2B (for example, ultra high net worth, B2B decision makers)",
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
    st.caption("Think TV, OOH or big digital bursts from other partners in the same markets and dates.")

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
    st.markdown(
        '<div class="question-heading">If you’re considering Brand Lift, when will the survey run?</div>',
        unsafe_allow_html=True,
    )
    options = [
        "During main body of campaign (good spread of exposure)",
        "After/close to the end of campaign",
        "Not planning Brand Lift / not sure",
    ]
    stored = answers["bls_timing"]
    if stored.startswith("During"):
        default_index = 0
    elif stored.startswith("After"):
        default_index = 1
    else:
        default_index = 2
    choice = st.radio("", options, index=default_index)
    if choice.startswith("During"):
        answers["bls_timing"] = "During main body of campaign"
    elif choice.startswith("After"):
        answers["bls_timing"] = "After/close to the end of campaign"
    else:
        answers["bls_timing"] = "Not planning Brand Lift / not sure"

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
        '<div class="question-heading">Do you want analyst detail (methods, caveats) in the output?</div>',
        unsafe_allow_html=True,
    )
    show_analyst_view = st.checkbox("", value=answers.get("show_analyst_view", False))
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
            "expectation": answers["expectation"],
            "other_media": answers["other_media"],
            "creative": answers["creative"],
            "niche_audience": answers["niche_audience"],
            "bls_timing": answers["bls_timing"],
        }

        score = compute_feasibility_score(final_answers)
        status_text, status_type = map_score_to_status(score)

        if status_type == "success":
            st.success(f"Feasibility: {status_text}")
        elif status_type == "warning":
            st.warning(f"Feasibility: {status_text}")
        else:
            st.error(f"Feasibility: {status_text}")

        rec = build_recommendation(final_answers)

        # ---------------------------------
        # Main recommendation blocks
        # ---------------------------------
        st.subheader("Recommended measurement approach")
        st.success(rec["primary"])

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

        # ---------------------------------
        # Premium summary block
        # ---------------------------------
        st.markdown("---")
        st.subheader("Email / notes summary")

        # A calm, human, blended summary drawing only on sticky-based logic.
        summary_lines = []

        summary_lines.append("Blis Measurement Recommendation")
        summary_lines.append("-------------------------------")
        summary_lines.append(f"Market: {final_answers['market']}")
        summary_lines.append(f"Objective: {final_answers['objective']}")
        summary_lines.append(f"Client expectation: {final_answers['expectation']}")
        summary_lines.append(f"IDs available: {final_answers['ids']}")
        summary_lines.append(f"Omnichannel: {final_answers['omnichannel']}")
        summary_lines.append(f"Budget band: {answers['budget_label'] or final_answers['budget_level']}")
        summary_lines.append(f"Planned impressions band: {answers['impressions_label'] or final_answers['impressions_level']}")
        summary_lines.append(f"Duration: {final_answers['duration']}")
        summary_lines.append(f"Niche / B2B audience: {final_answers['niche_audience']}")
        summary_lines.append(f"Other media in the mix: {final_answers['other_media']}")
        summary_lines.append(f"Creative quality: {final_answers['creative']}")
        summary_lines.append(f"Feasibility classification: {status_text}")
        summary_lines.append("")
        summary_lines.append("Recommended primary approach:")
        summary_lines.append(f"- {rec['primary']}")

        if rec["methods"]:
            summary_lines.append("")
            summary_lines.append("Suggested study types and thresholds:")
            for m in rec["methods"]:
                summary_lines.append(f"- {m}")

        if rec["risks"]:
            summary_lines.append("")
            summary_lines.append("Key risks and limiting factors to keep in mind:")
            for r in rec["risks"]:
                summary_lines.append(f"- {r}")

        if rec["alternatives"]:
            summary_lines.append("")
            summary_lines.append("Fallback options / backup plans:")
            for a in rec["alternatives"]:
                summary_lines.append(f"- {a}")

        summary_lines.append("")
        summary_lines.append(
            "Overall framing: position this as the most responsible measurement route given the "
            "budget, delivery, audience and data constraints. Be clear on what this setup can "
            "answer confidently and where results may be directional or sample-limited."
        )

        summary_text = "\n".join(summary_lines)

        st.code(summary_text, language="text")
        st.download_button(
            "Download summary as .txt",
            data=summary_text,
            file_name="blis_measurement_recommendation.txt",
        )

        st.caption(
            "Analysts can refine rules by editing compute_feasibility_score() and build_recommendation(). "
            "All thresholds and caveats here are taken directly from the shared sticky-note framework."
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
import streamlit as st

# -----------------------------
# Basic page config & styling
# -----------------------------

st.markdown(
    """
    <style>lov
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
    label = budget_label.lower()
    if "low" in label:
        return "Low"
    if "high" in label:
        return "High"
    return "Medium"


def get_impression_level(imp_label: str) -> str:
    label = imp_label.lower()
    if "<" in label or "0–" in label:
        return "Low"
    if "100k–" in label or "50k–" in label:
        return "Medium"
    return "High"


# -----------------------------
# Vendor-ish hints
# -----------------------------
def get_vendor_hint(market: str, objective: str) -> str:
    if "Brand awareness" in objective:
        return {
            "US": "Brand lift via established US panel/brand study partners.",
            "UK": "Brand lift via UK panel/brand study partners.",
            "EU": "Brand lift via EU panel providers.",
            "AU": "Brand lift via AU/NZ panel providers.",
            "NZ": "Brand lift via AU/NZ panel providers.",
            "Asia": "Brand lift via regional panel partners where available.",
            "Benelux": "Brand lift via EU/Benelux panel partners.",
            "Italy": "Brand lift via EU/IT panel partners.",
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
            "Italy": "Sales uplift using EU/IT retail/panel data.",
            "India": "Sales uplift using India retail/e-commerce data where enabled.",
            "Other": "Sales uplift using local retail/panel data where available.",
        }.get(market, "")
    if "App installs" in objective:
        return {
            "US": "App uplift via app analytics/MMP-style partners.",
            "UK": "App uplift via UK app analytics/MMP setups.",
            "EU": "App uplift via EU app analytics/MMP setups.",
            "AU": "App uplift via AU/NZ app analytics setups.",
            "NZ": "App uplift via AU/NZ app analytics setups.",
            "Asia": "App uplift via regional app analytics setups.",
            "Benelux": "App uplift via EU app analytics setups.",
            "Italy": "App uplift via EU/IT app analytics setups.",
            "India": "App uplift via India app analytics/MMP setups.",
            "Other": "App uplift via local app analytics/MMP setups.",
        }.get(market, "")
    return ""


# -----------------------------
# Feasibility scoring
# -----------------------------
def compute_feasibility_score(answers: dict) -> int:
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
        score -= 1

    return score


def map_score_to_status(score: int) -> tuple[str, str]:
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
    details, risks, alternatives, methods = [], [], [], []

    if objective == "Brand awareness / consideration":
        if ids != "Yes" or omnichannel == "Yes":
            primary = "Run an SHG-based Brand Lift / custom uplift study (min ~100k media spend)."
            methods.append("BLS SHG (minimum ~100k media spend).")
            methods.append("If SHG is not possible, use ODR-style survey (minimum ~40k).")
            details.append(
                "Channels without IDs and omnichannel activity require SHG-type brand lift or "
                "an ODR survey rather than pure ID-based BLS."
            )
        else:
            primary = "Run an ID-based Brand Lift Study (min ~30k media spend)."
            methods.append("BLS ID (minimum ~30k media spend).")
            methods.append("Optionally, BLS SHG (minimum ~100k) for omnichannel coverage.")
            methods.append("ODR survey (minimum ~40k) as an alternative panel-based approach.")
            details.append(
                "Use exposed vs control Brand Lift with IDs where available. "
                "If additional channels lack IDs, consider SHG."
            )

        if control == "No":
            risks.append("No control group defined – weakens the ability to prove incremental lift.")
            alternatives.append("Set up a holdout geo/audience, even if small, for future flights.")

        if budget_level == "Low":
            risks.append(
                "Running a BLS under ~30k spend can produce too small a sample. Example: "
                "£8 CPM on a £30k budget ≈ 240k impressions → 80k unique reach at freq 3 → "
                "800 clicks at 1% CTR → 80 completes at 10% completion – too small."
            )
            alternatives.append(
                "Increase spend beyond ~30k or treat any Brand Lift read as small-sample and directional."
            )

        if bls_timing == "After/close to the end of campaign":
            risks.append(
                "Running BLS after/close to the end of a campaign makes it hard to get a "
                "representative sample; subconscious recognition even 48 hours after exposure is limited."
            )

        if niche == "Yes":
            risks.append(
                "B2B/niche audience: likelihood of reaching enough respondents with BLS is very low."
            )
            alternatives.append(
                "Consider broader proxy audiences or alternative methods (qual, desk research, panel-based)."
            )

        risks.append(
            "Respondent experience: avoid too many answer options, overly long questions, or "
            "excessive survey length – these reduce completion and data quality."
        )

    elif objective == "Footfall / store visits":
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
                "Enable store visit data (via partners, beacons, Wi-Fi, or POS linkage) for future campaigns."
            )

    elif objective == "Sales / conversions":
        if offline_data == "Yes":
            primary = "Run a Sales Uplift study using merchant/product-level data."
            methods.append("Mastercard by merchant (minimum ~120k media spend).")
            methods.append("Circana by product (minimum ~100k media spend).")
            details.append(
                "Use matched exposed vs control at merchant/product level with panel or transaction data."
            )
        else:
            primary = (
                "Optimise towards performance KPIs (CPA/ROAS); full sales uplift not feasible without "
                "transaction data."
            )
            details.append(
                "Without sales data you can still optimise towards digital conversions but not run "
                "a formal sales uplift."
            )
            alternatives.append(
                "Work with the client to enable sales data sharing or partner connections for uplift work."
            )

    elif objective == "App installs / app usage":
        if offline_data == "Yes":
            primary = "Run an App Uplift study for key telco/app partners (min ~120k media spend)."
            methods.append("O2/VMO2-style app uplift (minimum ~120k media spend).")
            details.append(
                "Use app analytics to compare exposed vs control app usage/installs, respecting partner minimums."
            )
        else:
            primary = "Use standard app analytics and attribution with directional uplift checks."
            methods.append("Standard app attribution with simple uplift checks by geo/audience.")
            details.append(
                "Without dedicated app uplift partners, attribute installs to media and use trend differences "
                "as directional evidence."
            )

    else:
        primary = "Run an SHG/custom uplift approach where possible (min ~100k media spend)."
        methods.append("Other/custom uplift via SHG (minimum ~100k).")
        details.append(
            "For bespoke outcomes, use SHG/custom uplift as long as minimum volume is met; "
            "otherwise fall back to directional KPIs."
        )

    if budget_level == "Low":
        risks.append(
            "Budget/spend may be below the ~30k threshold – this can limit sample size and statistical power."
        )

    if budget_level == "Low" and impressions_level == "Low":
        risks.append(
            "Low spend AND low impressions – this is the 'Bermuda Triangle' where results often get lost."
        )
        alternatives.append(
            "Increase scale (budget/impressions) or avoid promising a formal uplift study; treat as exploratory."
        )

    if impressions_level == "Low":
        risks.append(
            "Number and density of impressions may be too low for robust learning – reach per postcode will be light."
        )

    if duration in ["< 1 week", "1–2 weeks"]:
        risks.append(
            "Duration is short – limited time to build reach and frequency, especially if there are bursts of activity."
        )

    if niche == "Yes":
        risks.append(
            "Niche audience (e.g., ultra high net worth, B2B decision makers) – budget vs reach trade-off is tough."
        )

    if other_media == "Yes":
        risks.append(
            "Heavy other media in the same period/markets makes it harder to isolate this campaign's impact."
        )
        alternatives.append(
            "Stagger campaigns, define clean test vs control regions, or apply geo designs that consider other media."
        )

    if creative == "Weak / poor fit / static banners only":
        risks.append(
            "Creative is weak or poorly aligned – even a perfect design may fail to show lift."
        )
        alternatives.append(
            "Improve or test creative first, then rerun measurement on a stronger platform."
        )
    elif creative == "Average / not tested yet":
        details.append(
            "Creative has not been fully tested – treat results as a read on both media and creative effectiveness."
        )

    if market in ["India", "Asia", "Other"]:
        risks.append(
            "Market data coverage and partner availability can vary – check in-market teams before promising specifics."
        )

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
st.caption("Blis' internal measurement concierge – designed with love.")
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
    options = ["< 100k", "100k–500k", "500k–1M", "1M+"]
    if answers["impressions_label"] and answers["impressions_label"] in options:
        default_index = options.index(answers["impressions_label"])
    else:
        default_index = 1
    impressions_label = st.selectbox("", options, index=default_index)
    answers["impressions_label"] = impressions_label
    answers["impressions_level"] = get_impression_level(impressions_label)

elif step == 7:
    st.markdown(
        '<div class="question-heading">Expected length of campaign?</div>',
        unsafe_allow_html=True,
    )
    options = ["< 1 week", "1–2 weeks", "2–4 weeks", "4+ weeks"]
    default_index = options.index(answers["duration"]) if answers["duration"] in options else 2
    duration = st.selectbox("", options, index=default_index)
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
    st.markdown(
        '<div class="question-heading">If you’re considering Brand Lift, when will the survey run?</div>',
        unsafe_allow_html=True,
    )
    options = [
        "During main body of campaign (good spread of exposure)",
        "After/close to the end of campaign",
        "Not planning Brand Lift / not sure",
    ]
    stored = answers["bls_timing"]
    if stored.startswith("During"):
        default_index = 0
    elif stored.startswith("After"):
        default_index = 1
    else:
        default_index = 2
    choice = st.radio("", options, index=default_index)
    if choice.startswith("During"):
        answers["bls_timing"] = "During main body of campaign"
    elif choice.startswith("After"):
        answers["bls_timing"] = "After/close to the end of campaign"
    else:
        answers["bls_timing"] = "Not planning Brand Lift / not sure"

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
    show_analyst_view = st.checkbox("", value=answers.get("show_analyst_view", False))
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

        score = compute_feasibility_score(final_answers)
        status_text, status_type = map_score_to_status(score)

        if status_type == "success":
            st.success(f"Feasibility: {status_text}")
        elif status_type == "warning":
            st.warning(f"Feasibility: {status_text}")
        else:
            st.error(f"Feasibility: {status_text}")

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
