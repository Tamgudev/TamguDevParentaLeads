import os
import pandas as pd
import serpapi

def get_html_template(title, content, active_page):
    # Navigation bar
    nav = f'''
    <nav style="margin-bottom: 20px;">
        <a href="index.html" style="margin-right: 15px; font-weight: {'bold' if active_page == 'leads' else 'normal'};">View Settings (Leads)</a>
        <a href="resources.html" style="font-weight: {'bold' if active_page == 'resources' else 'normal'};">View Resources</a>
    </nav>
    '''
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{ font-family: sans-serif; margin: 30px; background-color: #f8fafc; }}
            .table-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }}
            a {{ color: #2563eb; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        {nav}
        <div class="table-container">{content}</div>
    </body>
    </html>
    """

def fetch_data():
    api_key = os.getenv("SERPAPI_KEY")
    client = serpapi.Client(api_key=api_key)

    # 1. Fetch Business Settings (Google Maps)
    leads = []
    try:
        # We use a broader query to get 50 results
        results = client.search({"engine": "google_maps", "q": "day nurseries London", "num": 50, "hl": "en", "gl": "uk"})
        for item in results.get("local_results", []):
            leads.append({
                "Name": item.get("title", "N/A"),
                "Phone": f'<a href="tel:{item.get("phone")}">{item.get("phone", "N/A")}</a>',
                "Address": item.get("address", "N/A"),
                "Website": f'<a href="{item.get("website")}" target="_blank">Visit</a>' if item.get("website") else "N/A"
            })
    except Exception as e:
        print(f"Error fetching leads: {e}")

    # 2. Fetch Resources (Google Search)
    resources = []
    try:
        res = client.search({"engine": "google", "q": "early years childcare registration guides UK", "num": 10, "gl": "uk"})
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
    
    # Save Leads
    with open("index.html", "w", encoding="utf-8") as f:
        html = get_html_template("UK Early Years Leads", df_leads.to_html(index=False, escape=False), "leads")
        f.write(html)
        
    # Save Resources
    with open("resources.html", "w", encoding="utf-8") as f:
        html = get_html_template("Industry Resources", df_res.to_html(index=False, escape=False), "resources")
        f.write(html)

    print("Successfully generated index.html and resources.html!")
