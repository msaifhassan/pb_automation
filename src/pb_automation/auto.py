import re
import os
import dotenv
from datetime import datetime, timedelta
from playwright.sync_api import Playwright, sync_playwright, expect
dotenv.load_dotenv()


def login(playwright, username: str, password: str) -> tuple:
    """Logs into the club automation website and returns the page object."""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://centrecourt.clubautomation.com/")
    page.get_by_test_id("loginAccountUsername").click()
    page.get_by_test_id("loginAccountUsername").fill(username)
    page.get_by_test_id("loginAccountUsername").press("Tab")
    page.get_by_test_id("loginAccountPassword").fill(password)
    page.get_by_test_id("loginFormSubmitButton").click()
    return page, context, browser
    

def get_date():
    """Returns the date string a week from today in the format mm/dd/yyyy.
        Example: if today is tuesday, we pick next tuesday's date.
    """
    today = datetime.today()
    next_week = today + timedelta(weeks=1)
    return next_week.strftime("%m/%d/%Y")


def verify_successful(page) -> False:
    """Check to see if Confirm button is visible, if so return True, else False."""
    try:
        expect(page.get_by_role("button", name="Confirm")).to_be_visible(timeout=2000)
        page.get_by_role("button", name="Confirm").click()
        print("Reservation successful!")
        return True
    except:
        print("Reservation failed: Confirm button not found. Either you have already booked or no slots available.")
        return False
    

def run(page, reservation_date: str, duration: str = "120", reservation_time: str = "6:00pm") -> None:
    page.get_by_role("link", name="Reserve a Court").click()
    page.locator("a").filter(has_text="Racquetball").click()
    page.locator("#component_chosen").get_by_text("Tennis").click()
    page.locator("a").filter(has_text="All Surfaces").click()
    page.locator("#surface_chosen").get_by_text("Pickleball").click()
    
    
    page.locator("#timeFrom_chosen a").click()
    page.locator("#timeFrom_chosen").get_by_text("12:00 AM").first.click()
    page.locator("#timeTo_chosen a").click()
    page.locator("#timeTo_chosen").get_by_text("11:00 PM").click()
    
    page.locator('#date').fill(reservation_date)
    page.get_by_text(duration).click()
    
    page.get_by_role("button", name="Search").click()
    page.get_by_role("link", name=reservation_time).click()
    
    return verify_successful(page)
    

    

def main():
    with sync_playwright() as playwright:
        reservation_date = get_date()
        print(f"Reserving court for date: {reservation_date}")
        page, context, browser = login(playwright, os.getenv("PB_USERNAME"), os.getenv("PB_PASSWORD"))
        result = run(page, reservation_date, duration="120 Min", reservation_time="6:00pm")
        
        print(f"Result: {result}")
        
        page.get_by_role("button", name="Ok").click()
        page.get_by_role("link", name="Log Out").click()
        
        # ---------------------
        context.close()
        browser.close()
    

if __name__ == "__main__":
    main()