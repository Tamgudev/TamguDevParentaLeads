import os
import re
from datetime import datetime
import pandas as pd
import serpapi

def get_html_template(title, content, active_page):
    nav = f'''
    <nav style="margin-bottom: 20px; font-family: sans-serif;">
        <a href="index.html" style="margin-right: 15px; font-weight: {'bold' if active_page == 'leads' else 'normal'}; color: #2563eb; text-decoration: none;">View Settings (Leads)</a>
        <a href="resources.html" style="font-weight: {'bold' if active_page == 'resources' else 'normal'}; color: #2563eb; text-decoration: none;">View Resources</a>
    </nav>
    '''
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; background-color: #f8fafc; color: #1e293b; }}
            h1 {{ color: #0f172a; margin-bottom: 6px; font-size: 26px; }}
            .table-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-top: 20px; overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th, td {{ padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
            th {{ background-color: #0f172a; color: white; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }}
            tr:hover {{ background-color: #f1f5f9; }}
            a {{ color: #2563eb; font-weight: 600; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        {nav}
        <div class="table-container">{content}</div>
    </body>
    </html>
    """

def calculate_months_from_date(date_text):
    # Search for year and optional month in the text
    match_year = re.search(r'\b(20\d\d|19\d\d)\b', date_text)
    if not match_year:
        return None
    
    year = int(match_year.group(1))
    
    # Try to detect month
    months_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    month = 6  # Default to mid-year if month is not explicitly named
    for m_name, m_num in months_map.items():
        if m_name in date_text.lower():
            month = m_num
            break

    current_date = datetime(2026, 8, 16) # Current date reference
    target_date = datetime(year, month, 1)
    
    diff_months = (current_date.year - target_date.year) * 12 + (current_date.month - target_date.month)
    return max(0, diff_months)

def get_setting_age(client, name, address):
    # 1. Check maps extensions first
    # (Passed via item inspection if available)
    
    # 2. Fallback: Search government registries, website & news for opening date
    try:
        query = f'"{name}" nursery opening date OR Ofsted registration OR established'
        res = client.search({"engine": "google", "q": query, "num": 3, "gl": "uk"})
        
        combined_text = ""
        for item in res.get("organic_results", []):
            combined_text += " " + item.get("title", "") + " " + item.get("snippet", "")
            
        months = calculate_months_from_date(combined_text)
        if months is not None:
            if months == 0:
                return "Opened recently (< 1 month)"
            return f"{months} months open"
    except Exception:
        pass
        
    return "Established (Exact date unindexed)"

def fetch_data():
    api_key = os.getenv("SERPAPI_KEY")
    client = serpapi.Client(api_key=api_key)

    # 1. Fetch up to 50 Settings (Google Maps)
    leads = []
    try:
        results = client.search({
            "engine": "google_maps",
            "q": "day nurseries London",
            "num": 50,
            "hl": "en",
            "gl": "uk"
        })
        for item in results.get("local_results", []):
            name = item.get("title", "N/A")
            phone_raw = item.get("phone")
            phone = f'<a href="tel:{phone_raw}">{phone_raw}</a>' if phone_raw else "N/A"
            address = item.get("address", "N/A")
            
            website_raw = item.get("website")
            website = f'<a href="{website_raw}" target="_blank">Visit Website</a>' if website_raw else "N/A"
            
            # Check map extension/description first
            extensions = item.get("extensions", [])
            ext_text = " ".join(extensions) if isinstance(extensions, list) else str(extensions)
            ext_text += " " + str(item.get("description", ""))
            
            months = calculate_months_from_date(ext_text)
            if months is not None:
                age_info = f"{months} months open" if months > 0 else "Opened recently"
            else:
                # Fallback: check government/web sources
                age_info = get_setting_age(client, name, address)

            leads.append({
                "Setting Name": name,
                "Phone Number": phone,
                "Address": address,
                "Website": website,
                "Age / Opening Info": age_info
            })
    except Exception as e:
        print(f"Error fetching leads: {e}")

    # 2. Fetch Resources (Google Search)
    resources = []
    try:
        res = client.search({
            "engine": "google",
            "q": "early years childcare registration guides UK",
            "num": 15,
            "gl": "uk"
        })
        for item in res.get("organic_results", []):
            resources.append({
                "Title": item.get("title"),
                "Link": f'<a href="{item.get("link")}" target="_blank">Read More</a>',
                "Snippet": item.get("snippet", "")
            })
    except Exception as e:
        print(f"Error fetching resources: {e}")

    return pd.DataFrame(leads), pd.DataFrame(resources)

if __name__ == "__main__":
    df_leads, df_res = fetch_data()
    
    if df_leads.empty:
        df_leads = pd.DataFrame([{
            "Setting Name": "Awaiting Fresh Scan",
            "Phone Number": "N/A",
            "Address": "N/A",
            "Website": "N/A",
            "Age / Opening Info": "N/A"
        }])

    # Save Leads Page
    with open("index.html", "w", encoding="utf-8") as f:
        html = get_html_template("UK Early Years Leads", df_leads.to_html(index=False, escape=False), "leads")
        f.write(html)
        
    # Save Resources Page
    with open("resources.html", "w", encoding="utf-8") as f:
        html = get_html_template("Industry Resources", df_res.to_html(index=False, escape=False), "resources")
        f.write(html)

    print("Successfully generated index.html and resources.html with active government/web age lookups!")
