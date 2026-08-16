import os
import re
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

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

def extract_age_from_website(url):
    if not url or url == "N/A":
        return "Established Active Setting"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code != 200:
            return "Established Active Setting"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        # Look for establishment/opening patterns on the website text
        patterns = [
            r'(?:established|est\.?|founded|opened|opening|since)\s+(?:in\s+)?(\b(?:20\d\d|19\d\d)\b)',
            r'(\b(?:20\d\d|19\d\d)\b)\s+(?:saw the opening|was established|was founded)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                current_date = datetime(2026, 8, 16)
                diff_months = (current_date.year - year) * 12 + (current_date.month - 8)
                diff_months = max(0, diff_months)
                return f"{diff_months} months open" if diff_months > 0 else "Opened recently"

    except Exception:
        pass
    
    return "Established Active Setting"

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
        print("ERROR: SERPAPI_KEY environment variable is missing!")
        return pd.DataFrame(), pd.DataFrame()

    search_queries = [
        "day nurseries London",
        "day nurseries North London",
        "day nurseries South London"
    ]

    seen_keys = set()
    leads = []

    for q in search_queries:
        print(f"Executing search query: '{q}'...")
        try:
            params = {
                "engine": "google_maps",
                "q": q,
                "api_key": api_key
            }
            response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
            results = response.json()
            
            if "error" in results:
                print(f"SerpApi error for '{q}': {results['error']}")
                continue

            local_results = results.get("local_results", [])
            print(f"Found {len(local_results)} results for '{q}'")
            
            for item in local_results:
                name = item.get("title", "N/A")
                
                if is_corporate_chain(name):
                    continue

                address = item.get("address", "N/A")
                
                unique_key = (name.strip().lower(), address.strip().lower())
                if unique_key in seen_keys:
                    continue
                seen_keys.add(unique_key)

                phone_raw = item.get("phone")
                phone = f'<a href="tel:{phone_raw}">{phone_raw}</a>' if phone_raw else "N/A"
                
                website_raw = item.get("website")
                website = f'<a href="{website_raw}" target="_blank">Visit Website</a>' if website_raw else "N/A"
                
                # Extract age directly from the nursery's website content
                age_info = extract_age_from_website(website_raw)

                leads.append({
                    "Setting Name": name,
                    "Phone Number": phone,
                    "Address": address,
                    "Website": website,
                    "Age / Opening Info": age_info
                })
        except Exception as e:
            print(f"Error executing query '{q}': {e}")

    print(f"Total unique leads collected after filtering: {len(leads)}")

    # Fetch Resources
    resources = []
    try:
        res_params = {
            "engine": "google",
            "q": "early years childcare registration guides UK",
            "num": 10,
            "gl": "uk",
            "api_key": api_key
        }
        res_response = requests.get("https://serpapi.com/search.json", params=res_params, timeout=30)
        res = res_response.json()
        
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
        print("WARNING: df_leads is empty! Falling back to placeholder message.")
        df_leads = pd.DataFrame([{
            "Setting Name": "Awaiting Fresh Scan (Check GitHub Actions Log)",
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

    print("Successfully generated HTML pages.")
