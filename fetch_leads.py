import pandas as pd
import datetime

# Official UK Department for Education (GIAS) Live Dataset
url = "https://www.get-information-schools.service.gov.uk/Downloads/Extracts/edubasealldata.csv"

try:
    print("Fetching live DfE educational & early years dataset...")
    df = pd.read_csv(url, encoding='latin1', low_memory=False)

    # 1. STRICT FILTER: Only currently OPEN settings (excludes closed/deregistered)
    if 'EstablishmentStatus (name)' in df.columns:
        df = df[df['EstablishmentStatus (name)'] == 'Open']

    # 2. DATE FILTER: Settings opened within the last 3 years (1095 days)
    if 'OpenDate' in df.columns:
        df['OpenDate_parsed'] = pd.to_datetime(df['OpenDate'], dayfirst=True, errors='coerce')
        three_years_ago = pd.Timestamp.now() - pd.Timedelta(days=365 * 3)
        df = df[df['OpenDate_parsed'] >= three_years_ago]
        # Sort newest openings first
        df = df.sort_values(by='OpenDate_parsed', ascending=False)

    # 3. TYPE FILTER: Nursery & Early Years providers
    if 'PhaseOfEducation (name)' in df.columns and 'TypeOfEstablishment (name)' in df.columns:
        early_years_mask = (
            (df['PhaseOfEducation (name)'] == 'Nursery') | 
            (df['TypeOfEstablishment (name)'].str.contains('Nursery|Early Years|Childminder|Pre-School', case=False, na=False))
        )
        df = df[early_years_mask]

    # 4. SELECT & RENAME COLUMNS
    col_map = {
        'EstablishmentName': 'Setting Name',
        'OpenDate': 'Open Date',
        'Town (name)': 'Town',
        'Postcode': 'Postcode',
        'TelephoneNum': 'Telephone',
        'SchoolWebsite': 'Website',
        'URN': 'URN'
    }

    available_cols = [c for c in col_map.keys() if c in df.columns]
    df = df[available_cols].rename(columns=col_map)

    # Clean & format Phone numbers as clickable tel: links
    if 'Telephone' in df.columns:
        df['Telephone'] = df['Telephone'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df['Telephone'] = df['Telephone'].apply(
            lambda phone: f'<a href="tel:{phone}">{phone}</a>' if phone and phone.lower() != 'nan' and phone != '' else 'N/A'
        )

    # Clean & format Website links
    if 'Website' in df.columns:
        def format_website(web):
            web_str = str(web).strip()
            if not web_str or web_str.lower() in ['nan', 'none', 'n/a']:
                return 'N/A'
            url_target = web_str if web_str.startswith(('http://', 'https://')) else f'https://{web_str}'
            return f'<a href="{url_target}" target="_blank" rel="noopener noreferrer">Visit Website</a>'
        
        df['Website'] = df['Website'].apply(format_website)

    # Direct official DfE profile links
    if 'URN' in df.columns:
        df['DfE Profile'] = df['URN'].apply(
            lambda urn: f'<a href="https://www.get-information-schools.service.gov.uk/Establishments/Establishment/Details/{urn}" target="_blank" rel="noopener noreferrer">View Record</a>'
        )
        df = df.drop(columns=['URN'])

    # Format date display cleanly (YYYY-MM-DD)
    if 'Open Date' in df.columns:
        df['Open Date'] = pd.to_datetime(df['Open Date'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

    total_leads = len(df)
    print(f"Successfully filtered {total_leads} active settings opened in the last 3 years.")

except Exception as e:
    print(f"Error processing live dataset: {e}")
    total_leads = 0
    df = pd.DataFrame(columns=['Setting Name', 'Open Date', 'Town', 'Postcode', 'Telephone', 'Website', 'DfE Profile'])

# Generate HTML Table
if not df.empty:
    html_table = df.to_html(index=False, escape=False)
else:
    html_table = "<p style='padding: 20px; font-size: 16px; color: #dc2626;'>No active settings were found matching the criteria.</p>"

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Active UK Early Years Leads (Opened Last 3 Years)</title>
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
        <h1>UK Early Years Outreach Leads</h1>
        <p class="subtitle">Active Nursery & Early Years Settings Opened in England (Last 3 Years) | Total Leads: <span class="badge">{total_leads}</span></p>
    </div>
    <div class="table-container">
        {html_table}
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
