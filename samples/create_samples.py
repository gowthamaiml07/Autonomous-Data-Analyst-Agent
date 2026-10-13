"""Script to generate realistic sample datasets for InsightFlow AI."""
import os
import pandas as pd
import numpy as np

os.makedirs("samples", exist_ok=True)

# 1. Sales Data (sales_data.csv)
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
n_records = len(dates) * 3

regions = ["North America", "Europe", "Asia-Pacific", "Latin America"]
categories = {
    "Electronics": ["Smartphone Pro", "Ultra Laptop", "Wireless Headphones", "Smartwatch"],
    "Office Supplies": ["Ergonomic Chair", "Standing Desk", "Noise-Cancelling Pod", "Monitor Arm"],
    "Software": ["Cloud Storage Sub", "Security Suite", "BI Analytics Tool", "Team Chat License"]
}
sales_reps = ["Alice Chen", "Bob Miller", "Carlos Rossi", "Diana Prince", "Evan Wright", "Fatima Al-Mansoor"]
segments = ["Enterprise", "Mid-Market", "Small Business", "Consumer"]

data_sales = []
for _ in range(n_records):
    dt = np.random.choice(dates)
    reg = np.random.choice(regions, p=[0.4, 0.3, 0.2, 0.1])
    cat = np.random.choice(list(categories.keys()), p=[0.5, 0.3, 0.2])
    prod = np.random.choice(categories[cat])
    rep = np.random.choice(sales_reps)
    seg = np.random.choice(segments, p=[0.35, 0.3, 0.2, 0.15])
    
    if cat == "Electronics":
        price = np.random.choice([299, 499, 899, 1299])
        units = np.random.randint(1, 20)
        margin_pct = np.random.uniform(0.20, 0.45)
    elif cat == "Office Supplies":
        price = np.random.choice([89, 149, 320, 650])
        units = np.random.randint(2, 35)
        margin_pct = np.random.uniform(0.30, 0.60)
    else:
        price = np.random.choice([49, 99, 199, 499])
        units = np.random.randint(5, 50)
        margin_pct = np.random.uniform(0.65, 0.85)

    discount = np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], p=[0.5, 0.2, 0.15, 0.1, 0.05])
    effective_price = price * (1 - discount)
    revenue = round(effective_price * units, 2)
    cost = round(revenue * (1 - margin_pct), 2)
    profit = round(revenue - cost, 2)

    data_sales.append({
        "Date": pd.to_datetime(dt).strftime("%Y-%m-%d"),
        "Region": reg,
        "Product_Category": cat,
        "Product_Name": prod,
        "Sales_Rep": rep,
        "Customer_Segment": seg,
        "Units_Sold": units,
        "Unit_Price": price,
        "Discount_Pct": discount,
        "Revenue": revenue,
        "Cost": cost,
        "Profit": profit
    })

df_sales = pd.DataFrame(data_sales).sort_values("Date").reset_index(drop=True)
# Add small missing values or realistic variations
df_sales.loc[df_sales.sample(frac=0.01, random_state=42).index, "Discount_Pct"] = np.nan
df_sales.to_csv("samples/sales_data.csv", index=False)
print(f"Generated samples/sales_data.csv with {len(df_sales)} rows.")

# 2. Customer Churn (customer_churn.csv)
np.random.seed(101)
n_cust = 1200
contracts = ["Month-to-month", "One year", "Two year"]
tech_supp = ["Yes", "No", "No internet service"]
genders = ["Female", "Male"]

cust_records = []
for i in range(1, n_cust + 1):
    cid = f"CUST-{1000 + i}"
    gender = np.random.choice(genders)
    contract = np.random.choice(contracts, p=[0.55, 0.25, 0.20])
    tenure = np.random.randint(1, 72)
    monthly = round(np.random.uniform(20.0, 115.0), 2)
    total = round(monthly * tenure * np.random.uniform(0.95, 1.05), 2)
    tech = np.random.choice(tech_supp, p=[0.35, 0.50, 0.15])
    paperless = np.random.choice(["Yes", "No"], p=[0.6, 0.4])
    
    # Churn probability based on contract, tenure, tech support
    prob = 0.15
    if contract == "Month-to-month":
        prob += 0.25
    if tenure < 12:
        prob += 0.15
    if monthly > 80:
        prob += 0.10
    if tech == "No":
        prob += 0.10
    prob = min(max(prob, 0.05), 0.90)
    churn = "Yes" if np.random.rand() < prob else "No"
    
    cust_records.append({
        "CustomerID": cid,
        "Gender": gender,
        "Tenure_Months": tenure,
        "Contract_Type": contract,
        "Monthly_Charges": monthly,
        "Total_Charges": total,
        "Tech_Support": tech,
        "Paperless_Billing": paperless,
        "Churn": churn
    })

df_churn = pd.DataFrame(cust_records)
df_churn.loc[df_churn.sample(frac=0.015, random_state=42).index, "Total_Charges"] = np.nan
df_churn.to_csv("samples/customer_churn.csv", index=False)
print(f"Generated samples/customer_churn.csv with {len(df_churn)} rows.")

# 3. Student Performance (student_performance.xlsx) with multiple sheets
np.random.seed(202)
n_students = 600

scores = []
attendance = []
activities = []

for i in range(1, n_students + 1):
    sid = f"STU-{2000 + i}"
    gender = np.random.choice(["Female", "Male"])
    prep = np.random.choice(["None", "Completed"], p=[0.65, 0.35])
    
    base_math = 68 if prep == "Completed" else 58
    math_score = int(np.clip(np.random.normal(base_math, 14), 10, 100))
    read_score = int(np.clip(np.random.normal(math_score + 3, 10), 15, 100))
    write_score = int(np.clip(np.random.normal(read_score, 8), 15, 100))
    
    scores.append({
        "StudentID": sid,
        "Gender": gender,
        "Prep_Course": prep,
        "Math_Score": math_score,
        "Reading_Score": read_score,
        "Writing_Score": write_score
    })
    
    att_rate = round(np.clip(np.random.normal(0.88, 0.08), 0.50, 1.0), 3)
    absences = int(round((1 - att_rate) * 100))
    attendance.append({
        "StudentID": sid,
        "Attendance_Rate": att_rate,
        "Absences": absences
    })
    
    act = np.random.choice(["Robotics", "Debate", "Athletics", "Music", "None"], p=[0.2, 0.15, 0.25, 0.2, 0.2])
    role = "Member" if act != "None" and np.random.rand() > 0.2 else ("Leader" if act != "None" else "None")
    activities.append({
        "StudentID": sid,
        "Activity": act,
        "Role": role
    })

df_scores = pd.DataFrame(scores)
df_att = pd.DataFrame(attendance)
df_act = pd.DataFrame(activities)

with pd.ExcelWriter("samples/student_performance.xlsx", engine="openpyxl") as writer:
    df_scores.to_excel(writer, sheet_name="Exam_Scores", index=False)
    df_att.to_excel(writer, sheet_name="Attendance_Records", index=False)
    df_act.to_excel(writer, sheet_name="Extracurricular", index=False)

print(f"Generated samples/student_performance.xlsx with 3 sheets.")
