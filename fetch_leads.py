import pandas as pd
import requests
import datetime

# Download Ofsted Management Info / GIAS CSV
url = "https://files.ofsted.gov.uk/v1/file/50234567"  # Replace with direct Ofsted CSV URL if needed
df = pd.read_csv(url)

# Filter for settings registered in the last 365 days
cutoff = datetime.datetime.now() - datetime.timedelta(days=365)
df['Registration Date'] = pd.to_datetime(df['Registration Date'])
recent_leads = df[df['Registration Date'] >= cutoff]

# Generate simple HTML file
html_content = f"""
<!DOCTYPE html>
<html>
<head><title>New UK Settings Leads</title></head>
<body>
    <h1>UK Settings Opened in Last 12 Months</h1>
    {recent_leads.to_html(index=False)}
</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html_content)
