from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime
from models import db, Job
from app import app

# --- Setup Chrome Driver ---
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# --- Load the website ---
url = 'https://www.actuarylist.com'
driver.get(url)
time.sleep(3)  # wait for page to load

# --- Example: Accept cookies or scroll/load more ---
# Example: click "Load More" button multiple times
# (adjust selector as needed)

# while True:
#     try:
#         load_more = driver.find_element(By.XPATH, '//button[text()="Load More"]')
#         load_more.click()
#         time.sleep(2)
#     except:
#         break  # no more button

# --- Find job cards ---
jobs = driver.find_elements(By.CSS_SELECTOR, '.job-card')  # adjust selector to match site's HTML

print(f"Found {len(jobs)} jobs.")

with app.app_context():
    for job in jobs:
        try:
            title = job.find_element(By.CSS_SELECTOR, '.job-title').text.strip()
            company = job.find_element(By.CSS_SELECTOR, '.company').text.strip()
            location = job.find_element(By.CSS_SELECTOR, '.location').text.strip()
            posted = job.find_element(By.CSS_SELECTOR, '.posting-date').text.strip()
            link = job.find_element(By.TAG_NAME, 'a').get_attribute('href')
            
            # --- Clean & transform ---
            # Example: parse "posted X days ago"
            if "days ago" in posted:
                days = int(posted.split()[1])
                posting_date = datetime.now().date() - timedelta(days=days)
            else:
                posting_date = datetime.now().date()

            job_type = "Full-time"  # default, infer if available
            tags = ["Life", "Pricing"]  # example, parse real tags if available

            # --- Check for duplicates ---
            exists = Job.query.filter_by(title=title, company=company).first()
            if exists:
                print(f"Skipping duplicate: {title} at {company}")
                continue

            new_job = Job(
                title=title,
                company=company,
                location=location,
                posting_date=posting_date,
                job_type=job_type,
                tags=",".join(tags)
            )

            db.session.add(new_job)
            db.session.commit()
            print(f"Added: {title} at {company}")

        except Exception as e:
            print("Error scraping job:", e)

driver.quit()
print("Done scraping!")