import pandas as pd
import datetime

# Replace with direct live Ofsted / GIAS CSV URL when available
url = "https://files.ofsted.gov.uk/v1/file/50234567" 

try:
    df = pd.read_csv(url, encoding='latin1')
    # Filter and format real dataset columns here
except Exception as e:
    print(f"Could not load live CSV ({e}). Generating sample data with phone numbers...")
    data = {
        'Setting Name': ['Sunshine Day Nursery', 'Little Stars Pre-school', 'Bright Minds Childcare'],
        'Registration Date': [
            (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
            (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y-%m-%d'),
            (datetime.datetime.now() - datetime.timedelta(days=180)).strftime('%Y-%m-%d')
        ],
        'Postcode': ['SW1A 1AA', 'M1 1AE', 'B1 1BB'],
        'Telephone': [
            '<a href="tel:02079460123">020 7946 0123</a>',
            '<a href="tel:01614960456">0161 496 0456</a>',
            '<a href="tel:01214960789">0121 496 0789</a>'
        ],
        'Status': ['Active', 'Active', 'Active'],
        'Ofsted Record': [
            '<a href="https://reports.ofsted.gov.uk" target="_blank" rel="noopener noreferrer">View Record</a>',
            '<a href="https://reports.ofsted.gov.uk" target="_blank" rel="noopener noreferrer">View Record</a>',
            '<a href="https://reports.ofsted.gov.uk" target="_blank" rel="noopener noreferrer">View Record</a>'
        ]
    }
    df = pd.DataFrame(data)

# Generate HTML table allowing HTML formatting for links & phone numbers
html_table = df.to_html(index=False, escape=False)

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>New UK Settings Leads</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f8; }}
        h1 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #34495e; color: white; }}
        tr:hover {{ background-color: #f1f1f1; }}
        a {{ color: #2980b9; font-weight: bold; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>UK Settings Opened in Last 12 Months</h1>
    {html_table}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
