# ELECTRICITY USAGE ESTIMATOR - STREAMLIT + PYTHON

PROJECT FILES
- app.py: Streamlit interface and Python calculations
- requirements.txt: Required Python packages
- electricity_records.json: Persistent appliance data
- electricity_records.csv: Created/updated when records are saved

RUN IN VS CODE
1. Install Python 3.10 or newer.
2. Extract the ZIP and open the folder in VS Code.
3. Open Terminal > New Terminal.
4. Install packages:
      python -m pip install -r requirements.txt
5. Start the app:
      python -m streamlit run app.py
6. Open the local URL printed in the terminal (usually http://localhost:8501).

FEATURES
- Web-style interactive interface built with Streamlit
- Add appliance details and validate input
- Calculate daily energy (kWh) and cost (₹)
- Save records in JSON and CSV
- Search and category filtering
- Delete records
- Executive summary, status warning and charts
- Download CSV and JSON reports

FORMULAS
Daily energy (kWh) = Watts x Hours / 1000
Daily cost (₹) = Daily energy x tariff per kWh
