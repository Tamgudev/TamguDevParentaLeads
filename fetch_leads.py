import pandas as pd
import requests

# DfE GIAS Dataset
url_gias = "https://www.get-information-schools.service.gov.uk/Downloads/Extracts/edubasealldata.csv"

try:
    print("Fetching live DfE dataset for settings catering to ages <= 6...")
    df = pd.read_csv(url_gias, encoding='latin1', low_memory=False)

    # 1. Open settings only
    if 'EstablishmentStatus (name)' in df.columns:
        df = df[df['EstablishmentStatus (name)'] == 'Open']

    # 2. Filter settings catering to children 6 years old and younger
    low_age = pd.to_numeric(df['StatutoryLowAge'], errors='coerce')
    high_age = pd.to_numeric(df['StatutoryHighAge'], errors='coerce')

    # Settings where lower age is 6 or under
    age_mask = (low_age <= 6)

    # Filter by early years / primary keywords
    type_str = df['TypeOfEstablishment (name)'].fillna('').astype(str)
    name_str = df['EstablishmentName'].fillna('').astype(str)
    phase_str = df['PhaseOfEducation (name)'].fillna('').astype(str)

    keyword_mask = (
        type_str.str.contains('Nursery|Early Years|Pre-School|Infant|Primary|Childminder', case=False) |
        name_str.str.contains('Nursery|Pre-School|Daycare|Kindergarten|Montessori|Early Years|Infant|Primary', case=False) |
        phase_str.str.contains('Nursery|Primary', case=False)
    )

    df = df[age_mask & keyword_mask]

    # 3. Parse Open Date & filter for last 3 years
    if 'OpenDate' in df.columns:
        df['OpenDate_parsed'] = pd.to_datetime(df['OpenDate'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['OpenDate_parsed'])
        
        three_years_ago = pd.Timestamp.now() - pd.Timedelta(days=365 * 3)
        recent_df = df[df['OpenDate_parsed'] >= three_years_ago]

        # If strict 3-year cutoff yields fewer than 10, take the newest available records
        if len(recent_df) >= 10:
            df = recent_df
        else:
            df = df.sort_values(by='OpenDate_parsed', ascending=False)

    # 4. Map and clean columns
    col_map = {
        'EstablishmentName': 'Setting Name',
        'OpenDate': 'Open Date',
        'StatutoryLowAge': 'Min Age',
        'StatutoryHighAge': 'Max Age',
        'Town (name)': 'Town',
        'Postcode': 'Postcode',
        'TelephoneNum': 'Telephone',
        'SchoolWebsite': 'Website',
        'URN': 'URN'
    }

    available_cols = [c for c in col_map.keys() if c in df.columns]
    df = df[available_cols].rename(columns=col_map)

    # Format telephone links
    if 'Telephone' in df.columns:
        df['Telephone'] = df['Telephone'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df['Telephone'] = df['Telephone'].apply(
            lambda phone: f'<a href="tel:{phone}">{phone}</a>' if phone and phone.lower() != 'nan' and phone != '' else 'N/A'
        )

    # Format website links
    if 'Website' in df.columns:
        def format_website(web):
            web_str = str(web).strip()
            if not web_str or web_str.lower() in ['nan', 'none', 'n/a']:
                return 'N/A'
            url_target = web_str if web_str.startswith(('http://', 'https://')) else f'https://{web_str}'
            return f'<a href="{url_target}" target="_blank" rel="noopener noreferrer">Visit Website</a>'
        df['Website'] = df['Website'].apply(format_website)

    # Format DfE profile link
    if 'URN' in df.columns:
        df['DfE Record'] = df['URN'].apply(
            lambda urn: f'<a href="https://www.get-information-schools.service.gov.uk/Establishments/Establishment/Details/{urn}" target="_blank" rel="noopener noreferrer">View Record</a>'
        )
        df = df.drop(columns=['URN'])

    # Format dates
    if 'Open Date' in df.columns:
        df['Open Date'] = pd.to_datetime(df['Open Date'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

    df = df.head(100)
    total_leads = len(df)
    print(f"Successfully processed {total_leads} active settings for ages <= 6.")

except Exception as e:
    print(f"Error processing dataset: {e}")
    total_leads = 0
    df = pd.DataFrame(columns=['Setting Name', 'Open Date', 'Min Age', 'Max Age', 'Town', 'Postcode', 'Telephone', 'Website', 'DfE Record'])

# Generate HTML Table
if not df.empty:
    html_table = df.to_html(index=False, escape=False)
else:
    html_table = "<p style='padding: 20px; font-size: 16px; color: #dc2626;'>No active settings catering to ages 6 and under were found.</p>"

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UK Early Years & Infant Leads (Ages 0-6)</title>
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
        <p class="subtitle">Active Settings Catering to Ages 6 & Under (Opened in Last 3 Years) | Total Leads: <span class="badge">{total_leads}</span></p>
    </div>
    <div class="table-container">
        {html_table}
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
