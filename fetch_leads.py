import pandas as pd
import datetime

# Official Ofsted Early Years & Childcare Providers Dataset Link
# (Updated automatically via GOV.UK open data)
url = "https://assets.publishing.service.gov.uk/media/65f2d0111a1200001a357bb2/Childcare_providers_and_inspections_data_31_December_2023.csv"

try:
    print("Fetching live Ofsted Early Years Register dataset...")
    # Read Ofsted dataset
    df = pd.read_csv(url, encoding='latin1', low_memory=False)

    # 1. Filter for Active / Registered settings only
    if 'Provider Status' in df.columns:
        df = df[df['Provider Status'].str.lower() == 'active']

    # 2. Filter for Nursery / Early Years Provision
    if 'Provision Type' in df.columns:
        df = df[df['Provision Type'].str.contains('Childcare on Non-Domestic|Childcare on Domestic|Nursery', case=False, na=False)]

    # 3. Parse Registration Date & Filter strictly for last 3 years (1095 days)
    date_col = 'Registration Date' if 'Registration Date' in df.columns else 'First Registration Date'
    if date_col in df.columns:
        df['RegDate_parsed'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        three_years_ago = pd.Timestamp.now() - pd.Timedelta(days=365 * 3)
        df = df[df['RegDate_parsed'] >= three_years_ago]
        df = df.sort_values(by='RegDate_parsed', ascending=False)

    # 4. Column mapping
    col_map = {
        'Provider Name': 'Setting Name',
        date_col: 'Registration Date',
        'Town': 'Town',
        'Postcode': 'Postcode',
        'Telephone Number': 'Telephone',
        'Web Link': 'Website',
        'URN': 'URN'
    }

    available_cols = [c for c in col_map.keys() if c in df.columns]
    df = df[available_cols].rename(columns=col_map)

    # Clean phone numbers
    if 'Telephone' in df.columns:
        df['Telephone'] = df['Telephone'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df['Telephone'] = df['Telephone'].apply(
            lambda phone: f'<a href="tel:{phone}">{phone}</a>' if phone and phone.lower() != 'nan' and phone != '' else 'N/A'
        )

    # Clean website links
    if 'Website' in df.columns:
        def format_website(web):
            web_str = str(web).strip()
            if not web_str or web_str.lower() in ['nan', 'none', 'n/a']:
                return 'N/A'
            url_target = web_str if web_str.startswith(('http://', 'https://')) else f'https://{web_str}'
            return f'<a href="{url_target}" target="_blank" rel="noopener noreferrer">Visit Website</a>'
        df['Website'] = df['Website'].apply(format_website)

    # Direct Ofsted Report Links
    if 'URN' in df.columns:
        df['Ofsted Record'] = df['URN'].apply(
            lambda urn: f'<a href="https://reports.ofsted.gov.uk/provider/16/{urn}" target="_blank" rel="noopener noreferrer">View Ofsted Report</a>'
        )
        df = df.drop(columns=['URN'])

    # Format date
    if 'Registration Date' in df.columns:
        df['Registration Date'] = pd.to_datetime(df['Registration Date'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

    df = df.head(100)
    total_leads = len(df)
    print(f"Successfully loaded {total_leads} active settings registered with Ofsted in the last 3 years.")

except Exception as e:
    print(f"Error fetching Ofsted live data: {e}")
    total_leads = 0
    df = pd.DataFrame(columns=['Setting Name', 'Registration Date', 'Town', 'Postcode', 'Telephone', 'Website', 'Ofsted Record'])

# Generate HTML Table
if not df.empty:
    html_table = df.to_html(index=False, escape=False)
else:
    html_table = "<p style='padding: 20px; font-size: 16px; color: #dc2626;'>No active settings matching criteria were returned.</p>"

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Active Ofsted Early Years Leads (Last 3 Years)</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; background-color: #f8fafc; color: #1e293b; }}
        .header {{ margin-bottom: 25px; }}
        h1 {{ color: #0f172a; margin-bottom: 6px; font-size: 26px; }}
        .subtitle {{ font-size: 14px; color: #64748b; margin-top: 0; }}
        .badge {{ background-color: #2563eb; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 13px; }}
        .table-container {{ background: white; border-radius: 8px; overflow-x: auto; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }}
        table {{ border-collapse: collapse; width: 100%; text-align: left; }}
        th, td {{ padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
        th {{ background-color: #0f172a; color: #f8fafc; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }}
        tr:hover {{ background-color: #f1f5f9; }}
        a {{ color: #2563eb; font-weight: 600; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Ofsted Early Years Outreach Leads</h1>
        <p class="subtitle">Active Nurseries & Early Years Settings Registered in England (Last 3 Years) | Total Leads: <span class="badge">{total_leads}</span></p>
    </div>
    <div class="table-container">
        {html_table}
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
