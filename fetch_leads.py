import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

def fetch_directory_leads():
    # Example targeting a regional search page on a nursery directory
    url = "https://www.daynurseries.co.uk/daynurseries/search.cfm?searchregion=London"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch page")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    leads = []

    # Parse listing cards (adjust selectors based on the target site's HTML structure)
    for listing in soup.select('.nursery-card-class'):  # Replace with actual CSS class
        name = listing.select_title('.nursery-name').text.strip()
        address = listing.select_one('.nursery-address').text.strip()
        phone = listing.select_one('.nursery-phone').text.strip() if listing.select_one('.nursery-phone') else "N/A"
        
        leads.append({
            "Name": name,
            "Address": address,
            "Phone": phone,
            "Status": "Active / Pre-registration"
        })

    return leads

if __name__ == "__main__":
    leads_data = fetch_directory_leads()
    df = pd.DataFrame(leads_data)
    
    # Generate the updated index.html dashboard
    html_content = df.to_html(classes='table table-striped', index=False)
    with open("index.html", "w") as f:
        f.write(f"<html><body><h1>UK Early Years Outreach Leads</h1>{html_content}</body></html>")
