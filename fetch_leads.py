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
    match_year = re.search(r'\b(20\d\d|19\d\d)\b', date_text)
    if not match_year:
        return None
    
    year = int(match_year.group(1))
    months_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    month = 6 
    for m_name, m_num in months_map.items():
        if m_name in date_text.lower():
            month = m_num
            break

    current_date = datetime(2026, 8, 16)
    target_date = datetime(year, month, 1)
    
    diff_months = (current_date.year - target_date.year) * 12 + (current_date.month - target_date.month)
    return max(0, diff_months)

def is_corporate_chain(name):
    chains = [
        "bright horizons", "busy bees", "grandir", "family first", 
        "monkey puzzle", "banana moon", "kids planet", "partou", 
        "asquith", "kiddi caru", "toad hall", "fennies"
    ]
    name_lower = name.lower()
    for chain in chains:
        if chain in name_lower:
            return True
    return False

def fetch_data():
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("Error: SERPAPI_KEY not set.")
        return pd.DataFrame(), pd.DataFrame()

    client = serpapi.Client(api_key=api_key)

    # Multi-regional London queries to pull a robust list of unique leads
    search_queries = [
        "day nurseries North London",
        "day nurseries South London",
        "day nurseries East London",
        "day nurseries West London",
        "day nurseries Central London"
    ]

    seen_keys = set()
    leads = []

    for q in search_queries:
        try:
            results = client.search({
                "engine": "google_maps",
                "q": q,
                "num": 40,
                "hl": "en",
                "gl": "uk"
            })
            for item in results.get("local_results", []):
                name = item.get("title", "N/A")
                
                if is_corporate_chain(name):
                    continue

                address = item.get("address", "N/A")
                
                # Strict de-duplication key based on normalized name and address
                unique_key = (name.strip().lower(), address.strip().lower())
                if unique_key in seen_keys:
                    continue
                seen_keys.add(unique_key)

                phone_raw = item.get("phone")
                phone = f'<a href="tel:{phone_raw}">{phone_raw}</a>' if phone_raw else "N/A"
                
                website_raw = item.get("website")
                website = f'<a href="{website_raw}" target="_blank">Visit Website</a>' if website_raw else "N/A"
                
                extensions = item.get("extensions", [])
                ext_text = " ".join(extensions) if isinstance(extensions, list) else str(extensions)
                ext_text += " " + str(item.get("description", "")) + " " + str(item.get("snippet", ""))
                
                months = calculate_months_from_date(ext_text)
                if months is not None:
                    age_info = f"{months} months open" if months > 0 else "Opened recently"
                else:
                    age_info = "Established Active Setting"

                leads.append({
                    "Setting Name": name,
                    "Phone Number": phone,
                    "Address": address,
                    "Website": website,
                    "Age / Opening Info": age_info
                })
        except Exception as e:
            print(f"Error fetching query '{q}': {e}")

    # Fetch Resources (Google Search)
    resources = []
    try:
        res = client.search({
            "engine": "google",
            "q": "early years childcare registration guides UK",
            "num": 10,
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

    with open("index.html", "w", encoding="utf-8") as f:
        html = get_html_template("UK Early Years Leads", df_leads.to_html(index=False, escape=False), "leads")
        f.write(html)
        
    with open("resources.html", "w", encoding="utf-8") as f:
        html = get_html_template("Industry Resources", df_res.to_html(index=False, escape=False), "resources")
        f.write(html)

    print(f"Successfully generated index.html and resources.html with {len(df_leads)} leads!")
