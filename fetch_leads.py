import pandas as pd
import datetime

# Official UK Department for Education (GIAS) Live Data URL
url = "https://www.get-information-schools.service.gov.uk/Downloads/Extracts/edubasealldata.csv"

try:
    print("Fetching live DfE educational dataset...")
    df = pd.read_csv(url, encoding='latin1', low_memory=False)

    # 1. Keep Open settings only
    if 'EstablishmentStatus (name)' in df.columns:
        df = df[df['EstablishmentStatus (name)'].astype(str).str.lower() == 'open']

    # 2. Filter for settings catering to children 6 years old and under
    low_age = pd.to_numeric(df['StatutoryLowAge'], errors='coerce')
    high_age = pd.to_numeric(df['StatutoryHighAge'], errors='coerce')
    
    # StatutoryLowAge <= 6 OR StatutoryHighAge <= 6
    age_mask = (low_age <= 6) | (high_age <= 6)

    # Keywords matching Early Years, Nursery, Infant, and Primary
    type_str = df['TypeOfEstablishment (name)'].fillna('').astype(str)
    name_str = df['EstablishmentName'].fillna('').astype(str)
    phase_str = df['PhaseOfEducation (name)'].fillna('').astype(str)

    keyword_mask = (
        type_str.str.contains('Nursery|Early Years|Pre-School|Infant|Primary|Childminder', case=False) |
        name_str.str.contains('Nursery|Pre-School|Daycare|Kindergarten|Montessori|Early Years|Infant|Primary', case=False) |
        phase_str.str.contains('Nursery|Primary', case=False)
    )

    df = df[age_mask | keyword_mask].copy()

    # 3. Parse Open Dates and Sort by Newest Openings
    if 'OpenDate' in df.columns:
        df['OpenDate_parsed'] = pd.to_datetime(df['OpenDate'], dayfirst=True, errors='coerce')
        df = df.sort_values(by='OpenDate_parsed', ascending=False, na_position='last')

        # Calculate how long it's been open
        today = pd.Timestamp.now()
        def calculate_age_open(row):
            dt = row['OpenDate_parsed']
            if pd.isna(dt):
                return 'N/A'
            diff_days = (today - dt).days
            if diff_days < 365:
                return f"{diff_days} days ago"
            else:
                years = round(diff_days / 365, 1)
                return f"{years} years ago"
                
        df['Time Open'] = df.apply(calculate_age_open, axis=1)

    # 4. Select and Map Columns
    col_map = {
        'EstablishmentName': 'Setting Name',
        'Time Open': 'Time Open',
        'OpenDate': 'Open Date',
        'StatutoryLowAge': 'Min Age',
        'StatutoryHighAge': 'Max Age',
        'Postcode': 'Postcode',
        'TelephoneNum': 'Telephone',
        'SchoolWebsite': 'Website',
        'URN': 'URN'
    }

    available_cols = [c for c in col_map.keys() if c in df.columns]
    df = df[available_cols].rename(columns=col_map)

    # Clean & Format Telephones
    if 'Telephone' in df.columns:
        df['Telephone'] = df['Telephone'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df['Telephone'] = df['Telephone'].apply(
            lambda phone: f'<a href="tel:{phone}">{phone}</a>' if phone and phone.lower() != 'nan' and phone != '' else 'N/A'
        )

    # Clean & Format Websites
    if 'Website' in df.columns:
        def format_website(web):
            web_str = str(web).strip()
            if not web_str or web_str.lower() in ['nan', 'none', 'n/a']:
                return 'N/A'
            url_target = web_str if web_str.startswith(('http://', 'https://')) else f'https://{web_str}'
            return f'<a href="{url_target}" target="_blank" rel="noopener noreferrer">Visit Website</a>'
        df['Website'] = df['Website'].apply(format_website)

    # Clean DfE Record Profile Link
    if 'URN' in df.columns:
        df['DfE Profile'] = df['URN'].apply(
            lambda urn: f'<a href="https://www.get-information-schools.service.gov.uk/Establishments/Establishment/Details/{urn}" target="_blank" rel="noopener noreferrer">View Record</a>'
        )
        df = df.drop(columns=['URN'])

    # Limit view to top 100 newest leads
    df = df.head(100)
    total_leads = len(df)
    print(f"Successfully processed {total_leads} active early years settings.")

except Exception as e:
    print(f"Error processing dataset: {e}")
    total_leads = 0
    df = pd.DataFrame(columns=['Setting Name', 'Time Open', 'Open Date', 'Min Age', 'Max Age', 'Postcode', 'Telephone', 'Website', 'DfE Profile'])

# Generate Dashboard HTML
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
    <title>Active UK Early Years Leads (Ages 6 & Under)</title>
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
        <p class="subtitle">Active Settings Catering to Ages 6 & Under | Total Leads: <span class="badge">{total_leads}</span></p>
    </div>
    <div class="table-container">
        {html_table}
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
