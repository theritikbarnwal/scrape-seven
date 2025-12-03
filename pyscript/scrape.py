from playwright.sync_api import sync_playwright
import json
import re
from datetime import datetime

def scrape_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        page = context.new_page()

        jobs = []
        base_url = "https://careers.servicenow.com/jobs/"
        experience_regex = re.compile(
            r'\b(?:at least\s*\d+\+?\s*years?|minimum\s*\d+\+?\s*years?|\d+\+?\s*years?|'
            r'one year|two years?|three years?|four years?|five years?|six years?|seven years?|'
            r'eight years?|nine years?|ten years?)\b', re.IGNORECASE)

        for page_num in range(1, 2):
            url = f"{base_url}?page={page_num}#results"
            try:
                page.goto(url, wait_until='domcontentloaded')
                page.wait_for_function("document.querySelectorAll('div.card.card-job').length > 0", timeout=10000)

                job_cards = page.query_selector_all('div.card.card-job')

                for card in job_cards:
                    job_name = card.query_selector('h2.card-title')
                    job_name = job_name.inner_text().strip() if job_name else "NONE"

                    job_loc = card.query_selector('li.list-inline-item')
                    job_loc = job_loc.inner_text().strip() if job_loc else "NONE"

                    job_desc = "not mentioned"
                    experience = "not mentioned"

                    link = card.query_selector('a[href]')
                    jobLink = f"https://careers.servicenow.com{link.get_attribute('href')}" if link else ""

                    if jobLink:
                        try:
                            job_page = context.new_page()
                            job_page.goto(jobLink, wait_until='domcontentloaded')
                            page_text = job_page.inner_text('body')
                            matches = experience_regex.findall(page_text)
                            if matches:
                                experience = ', '.join(set(matches))
                            job_desc = jobLink
                            job_page.close()
                        except Exception as e:
                            print(f"Error reading job page {jobLink}: {e}")

                    jobs.append({
                        "Job": job_name,
                        "Location": job_loc,
                        "Experience": experience,
                        "Job Description": job_desc,
                        "ServiceNow Page": page_num
                    })

                print(f"Scraped page {page_num}")
            except Exception as e:
                print(f"Failed on page {page_num}: {e}")

        browser.close()

        timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")
        filename = f"PY_jobs-{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(jobs, f, indent=2)

        print(f"Saved {len(jobs)} jobs to {filename}")

# Run the function
scrape_jobs()