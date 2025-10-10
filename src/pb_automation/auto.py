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
    
    
def pick_time_slot(page) -> str:
    """Default reservation time is 6:00pm for weekdays and 8:00am for weekends.
       For weekday, looks links with text matching 6:00pm or 6:30pm or 7:00pm etc and returns the first match. 
    """
    
    weekday_preferred_times = [ "6:00pm", "6:30pm", "7:00pm", "7:30pm", "8:00pm" ]
    weekend_preferred_times = [ "8:00am", "8:30am", "9:00am", "9:30am", "10:00am" ]
    
    # logic to determine if today is a weekday or weekend
    today = datetime.today()
    if today.weekday() < 5:  # Monday to Friday are considered weekdays
        result = get_slot(page, weekday_preferred_times)
    else:  # Saturday and Sunday are considered weekends
        result = get_slot(page, weekend_preferred_times)
    return result
    
def get_slot(page, preferred_times) -> bool:
    for time in preferred_times:
        try:
            page.get_by_role("link", name=time).click()
            print(f"Successfully clicked on {time} time slot.")
            return True
        except:
            continue
    return False

def run(page, reservation_date: str, duration: str = "120") -> None:
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
    got_res = pick_time_slot(page)
    
    if not got_res:
        print("No preferred time slots available.")
        return False
    
    return verify_successful(page)
    

def main():
    with sync_playwright() as playwright:
        reservation_date = get_date()
        print(f"Reserving court for date: {reservation_date}")
        page, context, browser = login(playwright, os.getenv("PB_USERNAME"), os.getenv("PB_PASSWORD"))
        
        result = run(page, reservation_date, duration="120 Min")
        
        if not result:
            # Try again with 90 min duration
            print("Trying again with 90 min duration...")
            result = run(page, reservation_date, duration="90 Min")
        
        print(f"Result: {result}")
        
        page.get_by_role("button", name="Ok").click()
        page.get_by_role("link", name="Log Out").click()
        
        # ---------------------
        context.close()
        browser.close()
    

if __name__ == "__main__":
    main()