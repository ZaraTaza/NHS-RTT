# NHS RTT Waiting Times Analysis
# April 2025 – March 2026

# 1. Import libraries
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import BytesIO

# 2. Load, clean and validate data
def load_month(url, period):
    response = requests.get(url, timeout=60)
    
    df = pd.read_excel(BytesIO(response.content), sheet_name='ICB', header=13)

      # Remove non-ICB rows
    df = df[df['ICB Code'] != '-']

    # Remove unnecessary column
    df = df.drop(columns=['Unnamed: 0'])

    # Convert waiting-time variables to numeric
    df['Average (median) waiting time (in weeks)'] = pd.to_numeric(df['Average (median) waiting time (in weeks)'], errors='coerce')
    df['92nd percentile waiting time (in weeks)'] = pd.to_numeric(df['92nd percentile waiting time (in weeks)'], errors='coerce')

    # Calculate percentage over 18 weeks
    df['Total over 18 weeks'] = df['Total number of incomplete pathways'] - df['Total within 18 weeks']
    df['% over 18 weeks'] = (df['Total over 18 weeks'] / df['Total number of incomplete pathways'] * 100).round(2)
    df['Period'] = period
    return df

# Load files
files = [
    ("2025-04", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/02/Incomplete-Commissioner-Apr25-XLSX-4M-revised.xlsx"),
    ("2025-05", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/02/Incomplete-Commissioner-May25-XLSX-4M-revised.xlsx"),
    ("2025-06", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/02/Incomplete-Commissioner-Jun25-XLSX-4M-revised.xlsx"),
    ("2025-07", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/02/Incomplete-Commissioner-Jul25-XLSX-4M-revised-2.xlsx"),
    ("2025-08", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/02/Incomplete-Commissioner-Aug25-XLSX-4M-revised-2.xlsx"),
    ("2025-09", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/02/Incomplete-Commissioner-Sep25-XLSX-4M-revised.xlsx"),
    ("2025-10", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/12/Incomplete-Commissioner-Oct25-XLSX-4M-SrRW6y.xlsx"),
    ("2025-11", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/01/Incomplete-Commissioner-Nov25-XLSX-4M-1Xmjkk.xlsx"),
    ("2025-12", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/02/Incomplete-Commissioner-Dec25-XLSX-4M-6jPlxd.xlsx"),
    ("2026-01", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/03/Incomplete-Commissioner-Jan26-XLSX-4M-WL5BiP.xlsx"),
    ("2026-02", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/04/Incomplete-Commissioner-Feb26-XLSX-4M-9j03fJT.xlsx"),
    ("2026-03", "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/05/Incomplete-Commissioner-Mar26-XLSX-4M-Dc1i9U.xlsx"),
]

all_months = []

for period, url in files:
    print(f"Loading {period}...")
    df = load_month(url, period)
    all_months.append(df)
    print(f"  ✓ {len(df)} rows")

combined = pd.concat(all_months, ignore_index=True)
print(f"\nDone! Total rows: {len(combined):,}")

# 3. ICB analysis
# Aggregate monthly waiting-time data by ICB

icb_monthly = (
    combined.groupby(['ICB Name', 'ICB Code', 'Period'])
    .agg(
        Total_Waiting = ('Total number of incomplete pathways', 'sum'),
        Within_18     = ('Total within 18 weeks', 'sum'),
        Over_18       = ('Total over 18 weeks', 'sum'),
    )
    .reset_index()
)

# Calculate percentages within and over 18 weeks
icb_monthly['Pct_Over_18'] = (icb_monthly['Over_18'] / icb_monthly['Total_Waiting'] * 100).round(2)
icb_monthly['Pct_Within_18'] = (icb_monthly['Within_18'] / icb_monthly['Total_Waiting'] * 100).round(2)

print(f"ICB-month observations: {len(icb_monthly):,}")

# March 2026 ICB performance
mar26 = icb_monthly[icb_monthly["Period"] == "2026-03-01"]

# Best performing ICBs 
best_icbs = icb_monthly[icb_monthly['Period'] == '2026-03-01'].sort_values('Pct_Over_18', ascending=True)
print(best_icbs[['ICB Name', 'Pct_Over_18', 'Total_Waiting']].head(10))

# Worst performing ICBs 
worst_icbs = icb_monthly[icb_monthly['Period'] == '2026-03-01'].sort_values('Pct_Over_18', ascending=False)
print(worst_icbs[['ICB Name', 'Pct_Over_18', 'Total_Waiting']].head(10))

# Check the 65% interim target
met_target = mar26[mar26['Pct_Within_18'] >= 65]

failed_target = mar26[mar26['Pct_Within_18'] < 65]

print(f"{len(met_target)} out of {len(mar26)} ICBs met the 65% interim target")

print("\nICBs below the 65% interim target:")

print(failed_target[['ICB Name', 'Pct_Within_18', 'Total_Waiting']].sort_values('Pct_Within_18', ascending=True))

# National monthly trend
national_trend = icb_monthly.groupby('Period').agg(
    Avg_Pct_Within_18 = ('Pct_Within_18', 'mean'),
    Total_Waiting = ('Total_Waiting', 'sum')
).reset_index()

print(national_trend)

# 4. Visualisations for ICB analysis
# National average ICB performance
plt.figure(figsize=(12, 5))
plt.plot(national_trend['Period'], national_trend['Avg_Pct_Within_18'], 
         marker='o', color='steelblue', linewidth=2)
plt.axhline(y=65, color='red', linestyle='--', label='65% Interim Target')
plt.axhline(y=92, color='green', linestyle='--', label='92% Constitutional Standard')
plt.title('NHS England - Average % Within 18 Weeks (Apr 2025 - Mar 2026)')
plt.ylabel('% Within 18 Weeks')
plt.xlabel('Month')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
plt.savefig('national_trend.png', dpi=150, bbox_inches='tight')

apr25 = icb_monthly[icb_monthly['Period'] == '2025-04-01'][['ICB Code', 'ICB Name', 'Pct_Within_18']]
mar26 = icb_monthly[icb_monthly['Period'] == '2026-03-01'][['ICB Code', 'ICB Name', 'Pct_Within_18']]

# Merge the two DataFrames together on ICB Code
change = apr25.merge(mar26, on='ICB Code', suffixes=('_Apr25', '_Mar26'))

# Calculate the change
change["Change"] = (change['Pct_Within_18_Mar26'] - change['Pct_Within_18_Apr25'])

# Most improved ICBs
most_improved = change.sort_values('Change', ascending=False)
print("TOP 5 MOST IMPROVED:")
print(most_improved[['ICB Name_Apr25', 'Pct_Within_18_Apr25', 'Pct_Within_18_Mar26', 'Change']].head())

# Most worsened ICBs
most_worsened = change.sort_values('Change', ascending=True)
print("\nTOP 5 MOST WORSENED:")
print(most_worsened[['ICB Name_Apr25', 'Pct_Within_18_Apr25', 'Pct_Within_18_Mar26', 'Change']].head())

# 5. Regional analysis
region_mapping = {
    # North East and Yorkshire
    'QHM': 'North East and Yorkshire',  # North East and North Cumbria
    'QOQ': 'North East and Yorkshire',  # Humber and North Yorkshire
    'QWO': 'North East and Yorkshire',  # West Yorkshire
    
    # North West
    'QOP': 'North West',                # Greater Manchester
    'QYG': 'North West',                # Cheshire and Merseyside
    'QE1': 'North West',                # Lancashire and South Cumbria

    # Midlands
    'QHL': 'Midlands',                  # Birmingham and Solihull
    'QUA': 'Midlands',                  # Black Country
    'QWU': 'Midlands',                  # Coventry and Warwickshire
    'QJ2': 'Midlands',                  # Derby and Derbyshire
    'QGH': 'Midlands',                  # Herefordshire and Worcestershire
    'QK1': 'Midlands',                  # Leicester, Leicestershire and Rutland
    'QJM': 'Midlands',                  # Lincolnshire
    'QPM': 'Midlands',                  # Northamptonshire
    'QT1': 'Midlands',                  # Nottingham and Nottinghamshire
    'QOC': 'Midlands',                  # Shropshire, Telford and Wrekin
    'QNC': 'Midlands',                  # Staffordshire and Stoke-on-Trent

    # East of England
    'QH8': 'East of England',           # Mid and South Essex
    'QMM': 'East of England',           # Norfolk and Waveney
    'QJG': 'East of England',           # Suffolk and North East Essex
    'QHG': 'East of England',           # Bedfordshire, Luton and Milton Keynes
    'QUE': 'East of England',           # Cambridgeshire and Peterborough

    # London
    'QKK': 'London',                    # South East London
    'QMF': 'London',                    # North East London
    'QMJ': 'London',                    # North Central London
    'QRV': 'London',                    # North West London
    'QWE': 'London',                    # South West London
    'QM7': 'London',                    # Hertfordshire and West Essex 

    # South East
    'QNQ': 'South East',                # Frimley
    'QKS': 'South East',                # Kent and Medway
    'QNX': 'South East',                # Sussex
    'QU9': 'South East',                # Buckinghamshire, Oxfordshire and Berkshire West
    'QRL': 'South East',                # Hampshire and Isle of Wight
    'QXU': 'South East',                # Surrey Heartlands

    # South West
    'QOX': 'South West',                # Bath, North East Somerset, Swindon and Wiltshire
    'QT6': 'South West',                # Cornwall and Isles of Scilly
    'QJK': 'South West',                # Devon
    'QUY': 'South West',                # Bristol, North Somerset and South Gloucestershire
    'QR1': 'South West',                # Gloucestershire
    'QSL': 'South West',                # Somerset
    'QVV': 'South West',                # Dorset
}

# Regional mapping
icb_monthly['Region'] = icb_monthly['ICB Code'].map(region_mapping)

# Check that all ICBs were mapped
unmapped = icb_monthly[icb_monthly['Region'].isna()][['ICB Code', 'ICB Name']].drop_duplicates()
print(f"{len(unmapped)} ICBs unmapped")

if len(unmapped) > 0:
    print(unmapped)

# Aggregate ICB data by region and month
regional_monthly = icb_monthly.groupby(['Region', 'Period']).agg( Total_Waiting = ('Total_Waiting', 'sum'), Within_18 = ('Within_18', 'sum'), Over_18 = ('Over_18', 'sum') ).reset_index()

regional_monthly['Pct_Within_18'] = (regional_monthly['Within_18'] / regional_monthly['Total_Waiting'] * 100).round(2)

# Regional performance for March 2026
mar26_regional = regional_monthly[regional_monthly['Period'] == '2026-03-01']
print(mar26_regional[['Region', 'Pct_Within_18', 'Total_Waiting']].sort_values('Pct_Within_18', ascending=False))

# 6. Visualisations for regional analysis
mar26_regional_sorted = mar26_regional.sort_values('Pct_Within_18', ascending=True)

plt.figure(figsize=(10, 6))
colors = ['red' if x < 65 else 'steelblue' for x in mar26_regional_sorted['Pct_Within_18']]
plt.barh(mar26_regional_sorted['Region'], mar26_regional_sorted['Pct_Within_18'], color=colors)
plt.axvline(x=65, color='red', linestyle='--', label='65% Interim Target')
plt.axvline(x=92, color='green', linestyle='--', label='92% Constitutional Standard')
plt.title('NHS Regions - % Within 18 Weeks (March 2026)')
plt.xlabel('% Within 18 Weeks')
plt.xlim(0, 100)
plt.legend()
plt.tight_layout()
plt.show()

plt.savefig('regional_march2026.png', dpi=150, bbox_inches='tight')

icb_monthly.to_csv('icb_monthly_clean.csv', index=False)
regional_monthly.to_csv('regional_monthly_clean.csv', index=False)
print("All saved!")

# Regional performance trend
plt.figure(figsize=(12, 6))

for region in regional_monthly['Region'].unique():
    data = regional_monthly[regional_monthly['Region'] == region]
    plt.plot(data['Period'], data['Pct_Within_18'], marker='o', label=region)

plt.axhline(y=65, color='red', linestyle='--', label='65% Interim Target')
plt.title('NHS Regions - % Within 18 Weeks Trend (Apr 2025 - Mar 2026)')
plt.ylabel('% Within 18 Weeks')
plt.xlabel('Month')
plt.xticks(rotation=45)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
plt.savefig('regional_trend.png', dpi=150, bbox_inches='tight')

# 7. Export Results
icb_monthly.to_csv('icb_monthly_clean.csv', index=False)
regional_monthly.to_csv('regional_monthly_clean.csv', index=False)
change.to_csv('icb_change.csv', index=False)
national_trend.to_csv('national_trend.csv', index=False)
print("All saved!")
