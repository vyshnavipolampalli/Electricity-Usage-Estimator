import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
JSON_FILE = BASE_DIR / "electricity_records.json"
CSV_FILE = BASE_DIR / "electricity_records.csv"

st.set_page_config(
    page_title="Electricity Usage Estimator",
    page_icon="⚡",
    layout="wide"
)


def load_records():
    """Load saved appliance records, or start with an empty list."""
    try:
        with JSON_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            valid = []
            for item in data:
                try:
                    name = str(item["name"]).strip()
                    watts = float(item["watts"])
                    hours = float(item["hours"])
                    rate = float(item["rate"])
                    category = str(item.get("category", "Other"))
                    if name and 0 < watts <= 100000 and 0 < hours <= 24 and 0 <= rate <= 1000:
                        valid.append({
                            "name": name,
                            "category": category,
                            "watts": watts,
                            "hours": hours,
                            "rate": rate
                        })
                except (KeyError, TypeError, ValueError):
                    continue
            return valid
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    save_records([])
    return []


def save_records(records):
    """Persist records to JSON and CSV."""
    with JSON_FILE.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)
    pd.DataFrame(records, columns=["name", "category", "watts", "hours", "rate"]).to_csv(
        CSV_FILE, index=False
    )


def calculate_frame(records):
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["Daily Energy (kWh)"] = df["watts"] * df["hours"] / 1000
    df["Daily Cost (₹)"] = df["Daily Energy (kWh)"] * df["rate"]
    return df


if "records" not in st.session_state:
    st.session_state.records = load_records()

records = st.session_state.records

st.markdown("""
<style>
.main {background-color: #f5faf6;}
.block-container {padding-top: 2rem;}
.hero {
    background: linear-gradient(110deg, #105b38, #23965c);
    color: white; padding: 26px 30px; border-radius: 16px;
    margin-bottom: 22px;
}
.hero h1 {color: white; margin: 0;}
.hero p {color: #e4f5e9; margin-bottom: 0;}
div[data-testid="stMetric"] {
    background: white; padding: 15px; border-radius: 12px;
    border: 1px solid #e2eee5;
}
</style>
<div class="hero">
    <h1>⚡ Electricity Usage Estimator</h1>
    <p>GreenFuture Hack · Project 43 · Track appliance energy and estimated costs</p>
</div>
""", unsafe_allow_html=True)

df = calculate_frame(records)
total_energy = float(df["Daily Energy (kWh)"].sum()) if not df.empty else 0
total_cost = float(df["Daily Cost (₹)"].sum()) if not df.empty else 0
average_energy = total_energy / len(df) if not df.empty else 0

m1, m2, m3 = st.columns(3)
m1.metric("Appliances recorded", len(records))
m2.metric("Daily energy use", f"{total_energy:.2f} kWh")
m3.metric("Estimated daily cost", f"₹{total_cost:.2f}")

st.divider()
add_tab, records_tab, summary_tab = st.tabs(
    ["➕ Add Appliance", "📋 Records & Search", "📊 Summary & Charts"]
)

with add_tab:
    st.subheader("Enter appliance details")
    with st.form("appliance_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Appliance name", placeholder="Example: Ceiling fan")
            watts = st.number_input("Power rating (watts)", min_value=1.0, max_value=100000.0, value=75.0, step=1.0)
            hours = st.number_input("Usage per day (hours)", min_value=0.1, max_value=24.0, value=8.0, step=0.5)
        with col2:
            category = st.selectbox(
                "Category",
                ["Kitchen", "Lighting", "Cooling", "Entertainment", "Other"]
            )
            rate = st.number_input("Electricity rate (₹ per kWh)", min_value=0.0, max_value=1000.0, value=8.0, step=0.5)
            st.info("Energy (kWh) = Watts × Hours ÷ 1000")
        submitted = st.form_submit_button("Calculate and Save", type="primary", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Please enter an appliance name.")
        else:
            new_record = {
                "name": name.strip(),
                "category": category,
                "watts": float(watts),
                "hours": float(hours),
                "rate": float(rate)
            }
            records.append(new_record)
            save_records(records)
            st.success(
                f"Saved {name}: {(watts * hours / 1000):.3f} kWh/day | "
                f"₹{(watts * hours / 1000 * rate):.2f}/day"
            )
            st.rerun()

with records_tab:
    st.subheader("Appliance records")
    if records:
        search_col, category_col = st.columns([2, 1])
        search_text = search_col.text_input("Search by appliance name")
        categories = ["All"] + sorted({r["category"] for r in records})
        selected_category = category_col.selectbox("Filter category", categories)

        filtered = df.copy()
        if search_text:
            filtered = filtered[filtered["name"].str.contains(search_text, case=False, na=False)]
        if selected_category != "All":
            filtered = filtered[filtered["category"] == selected_category]

        display = filtered.rename(columns={
            "name": "Appliance",
            "category": "Category",
            "watts": "Watts",
            "hours": "Hours/day",
            "rate": "Rate (₹/kWh)"
        })
        st.dataframe(
            display[["Appliance", "Category", "Watts", "Hours/day", "Rate (₹/kWh)",
                     "Daily Energy (kWh)", "Daily Cost (₹)"]],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download CSV report",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="electricity_usage_report.csv",
            mime="text/csv"
        )

        st.markdown("**Delete a record**")
        labels = [f"{i + 1}. {r['name']} ({r['category']})" for i, r in enumerate(records)]
        selected_to_delete = st.selectbox("Choose appliance", labels)
        if st.button("Delete selected appliance", type="secondary"):
            index = labels.index(selected_to_delete)
            deleted = records.pop(index)
            save_records(records)
            st.success(f"Deleted {deleted['name']}.")
            st.rerun()
    else:
        st.info("No appliances have been added yet. Use the Add Appliance tab to begin.")

with summary_tab:
    st.subheader("Executive summary")
    if records:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total appliances", len(records))
        c2.metric("Average energy per appliance", f"{average_energy:.3f} kWh")
        c3.metric("Estimated monthly cost (30 days)", f"₹{total_cost * 30:.2f}")

        if total_cost > 100:
            st.warning("Daily estimated cost is above ₹100. Consider reviewing high-usage appliances.")
        else:
            st.success("Daily estimated cost is ₹100 or below.")

        st.markdown("#### Daily energy use by appliance")
        chart_data = df.set_index("name")[["Daily Energy (kWh)"]]
        st.bar_chart(chart_data)

        st.markdown("#### Daily estimated cost by category")
        category_data = df.groupby("category")["Daily Cost (₹)"].sum()
        st.bar_chart(category_data)
    else:
        st.info("Add appliances to view summary metrics and charts.")

with st.sidebar:
    st.header("🌱 About the project")
    st.write(
        "This application estimates electricity consumption and cost using "
        "appliance wattage, daily usage hours and the electricity tariff."
    )
    st.caption("Formula: kWh = Watts × Hours ÷ 1000")
    st.divider()
    if st.button("Export saved data as JSON"):
        st.download_button(
            "Download JSON",
            data=json.dumps(records, indent=4),
            file_name="electricity_records.json",
            mime="application/json"
        )
    if st.button("Clear all records"):
        st.session_state.confirm_clear = True
    if st.session_state.get("confirm_clear", False):
        st.warning("Are you sure you want to delete all saved records?")
        yes_col, no_col = st.columns(2)
        if yes_col.button("Yes, clear"):
            st.session_state.records = []
            save_records([])
            st.session_state.confirm_clear = False
            st.rerun()
        if no_col.button("Cancel"):
            st.session_state.confirm_clear = False
            st.rerun()

st.caption("Note: This is an estimate. Actual electricity bills may include fixed charges, taxes and slab rates.")
