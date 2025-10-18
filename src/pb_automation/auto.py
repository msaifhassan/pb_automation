import re
import os
import dotenv
import time
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from playwright.sync_api import Playwright, sync_playwright, expect
dotenv.load_dotenv()


def get_date():
    """Returns the date string a week from today in the format mm/dd/yyyy.
        Example: if today is tuesday, we pick next tuesday's date.
    """
    today = datetime.today()
    next_week = today + timedelta(weeks=1)
    return next_week.strftime("%m/%d/%Y")

def log(message: str):
    print(message)
    messages.append(message)
    
    
messages = []
reservation_date = get_date()
test_mode = True if os.getenv("TEST_MODE", "false").lower() == "true" else False
log(f"Test mode is {'on' if test_mode else 'off'}.")



def login(playwright, username: str, password: str) -> tuple:
    """Logs into the club automation website and returns the page object."""
    
    headless = not test_mode # when test_mode is True, headless is False (i.e., show the browser)
    log(f"Running in headless mode: {headless}")
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://centrecourt.clubautomation.com/")
    page.get_by_test_id("loginAccountUsername").click()
    page.get_by_test_id("loginAccountUsername").fill(username)
    page.get_by_test_id("loginAccountUsername").press("Tab")
    page.get_by_test_id("loginAccountPassword").fill(password)
    page.get_by_test_id("loginFormSubmitButton").click()
    return page, context, browser
    


def verify_successful(page) -> False:
    """Check to see if Confirm button is visible, if so return True, else False."""
    try:
        expect(page.get_by_role("button", name="Confirm")).to_be_visible(timeout=2000)
        page.get_by_role("button", name="Confirm").click()
        log("Reservation successful!")
        page.get_by_role("button", name="Ok").click()
        page.get_by_role("link", name="Log Out").click()
        return True
    except:
        log("Reservation failed: Confirm button not found. Either you have already booked or no slots available.")
        try:
            page.get_by_role("button", name="Ok").click()
        except:
            pass
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


def unsuccessful_results(page) -> bool:
    try:
        expect(page.get_by_text("No available times based on your search criteria.")).to_be_visible(timeout=200)
        log("No available times based on your search criteria.")
        return True
    except:
        return False
    
def get_slot(page, preferred_times) -> bool:
    for time in preferred_times:
        try:
            page.get_by_role("link", name=time).click(timeout=1500)
            log(f"Successfully clicked on {time} time slot.")
            return True
        except:
            if unsuccessful_results(page):
                return False
            log(f"Time slot {time} not available, trying next preferred time...")
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
        log("No preferred time slots available.")
        return False
    
    return verify_successful(page)
    

def close_browser(browser, context):
    context.close()
    browser.close()
    
    
def send_email(messages: list, result: bool):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart("alternative")
    res_msg = "Successful" if result else "Unsuccessful"
    msg["Subject"] = f"Pickleball Reservation {res_msg}: {reservation_date}"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    text = "\n".join(messages)
    part = MIMEText(text, "plain")
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
        
        
def after_7am_wait():
    """Wait until 7am CST to proceed."""
    if test_mode:
        log("Test mode is on, skipping wait until 7am CST.")
        return
    
    while True:
        now = datetime.now(ZoneInfo("America/Chicago"))
        if now.hour >= 7:
            log("It's now after 7am CST, proceeding with reservation...")
            break
        else:
            print(f"Current CST time: {now.strftime('%Y-%m-%d %H:%M:%S')}. Waiting until 7am CST...")
            time.sleep(.25)

def main():
    with sync_playwright() as playwright:
        log("Starting the reservation process...")
        log(f"Reservation Date: {reservation_date}")
        page, context, browser = login(playwright, os.getenv("PB_USERNAME"), os.getenv("PB_PASSWORD"))
        after_7am_wait()
                
        result = run(page, reservation_date, duration="120 Min")
        if not result:
            # Try again with 90 min duration
            message = "Trying again with 90 min duration..."
            print(message)
            messages.append(message)
            
            result = run(page, reservation_date, duration="90 Min")
        
        print(f"Final Result: {result}")
        messages.append(f"Final Result: {result}")
            
        # ---------------------
        close_browser(browser, context)
        send_email(messages, result)
    

if __name__ == "__main__":
    main()
