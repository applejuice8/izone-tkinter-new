from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from pathlib import Path
import pandas as pd
import keyring
import time

# Note 
'''
if subject has 2 lecture slots together, not supported currently

normally thead
period-time-str = "TUE-20:00:00-22:00:00"

digital economy thead
period-time-str = "TUE-20:00:00-22:00:00|THU-20:00:00-22:00:00"
'''

class SlotScraper:
    def __init__(self, driver, headless, my_subjects):
        if driver:
            self.driver = driver
        else:
            self.driver = self.init_driver(headless)

        self.wait = WebDriverWait(self.driver, 2)
        self.data = []
        self.my_subjects = my_subjects

    def init_driver(self, headless):
        print('Setting up webdriver...')

        options = Options()
        if headless:
            options.add_argument('--headless')

        # Use Service with WebDriver Manager
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    
    def get_page(self, testing):
        print('Fetching page...')

        if testing:
            print()
            self.driver.get(Path('test_html/3choose.html').resolve().as_uri())
        else:
            self.driver.get('https://izone.sunway.edu.my/login')
    
    def login(self):
        print('Logging in...')

        input_un = self.wait.until(EC.presence_of_element_located((By.ID, 'student_uid')))
        input_pw = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
        submit_btn = self.wait.until(EC.presence_of_element_located((By.ID, 'submit')))

        input_un.send_keys(keyring.get_password('izone', 'username'))
        input_pw.send_keys(keyring.get_password('izone', 'password'))
        submit_btn.click()

    def enroll(self):
        print('Enrolling...')

        while True:
            try:
                # Enroll btn
                self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@id="panel-dashboard-profile"]//a[@class="btn btn-default"]'))
                ).click()
                break

            except TimeoutException:
                # Reload
                self.wait.until(
                    EC.element_to_be_clickable((By.ID, 'reloadUrl'))
                ).click()
                print('Button not found. Refreshing...')
    
    def check_tnc(self):
        try:
            self.wait.until(
                EC.element_to_be_clickable((By.ID, 'chk_confirm'))
            ).click()
        except TimeoutException:  # If chosen
            self.driver.find_element(By.XPATH, '//button[@name="btn_edit"]').click()
    
    def scrape(self):
        subjects = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'mySubject')))
        
        for subject in subjects:
            name = subject.find_element(By.XPATH, './/label').text

            # Check if its my subject
            if (self.isMySubject(name)):
                print(f'Scraping "{name}"...')

                info = {}
                info['Subject'] = name

                # Expand dropdowns
                self.expand_dd(subject)    

                # Scrape lectures
                tables = subject.find_elements(By.XPATH, './/table')
                self.scrape_section(tables[0], info, 'Lecture')

                # Scrape practicals
                try:
                    self.scrape_section(tables[1], info, 'Practical')
                except IndexError:
                    pass

                # Scrape workshops
                try:
                    self.scrape_section(tables[2], info, 'Workshop')
                except IndexError:
                    pass

    def scrape_section(self, table, info, class_type):
        info['Class Type'] = class_type

        theads = table.find_elements(By.XPATH, './/thead[@class="izoneThead"]')
        for thead in theads:
            text = thead.text

            # Skip groups that are full
            if 'Temporarily Full' in text:
                continue

            # Scrape group number, teacher
            info['Group Number'], info['Teacher'] = thead.find_element(By.XPATH, './/strong').text.split(' : ')

            # Scrape day, time
            time_data = thead.find_element(By.XPATH, './/input').get_attribute('period-time-str')
            info['Day'], info['Start Time'], info['End Time'] = time_data.split('-')

            # Data cleaning
            info['Start Time'] = info['Start Time'][:-3]
            info['End Time'] = info['End Time'][:-3]

            # Add to data
            self.data.append(info.copy())

    def export(self):
        print('\nExporting data...')
        try:
            df = pd.DataFrame(self.data)
            df.index += 1
            df.to_csv('scraped_files/slots.csv', index=False)
            print(f'Data successfully exported to "slots.csv"')

        except Exception as e:
            print(e)
            input('Export error. Continue? ')

    # Helper Functions
    def isMySubject(self, name):
        for myS in self.my_subjects:
            if myS in name.lower():
                return True
        return False

    def expand_dd(self, subject):
        panel_groups = subject.find_elements(By.CLASS_NAME, 'panel-group')
        for panel_group in panel_groups:
            
            # Try expand dropdown
            try:
                panel_group.find_element(By.XPATH, './/span[contains(@class, "glyphicon-chevron-down")]').click()
                time.sleep(0.2)
            except NoSuchElementException:
                pass

def start_scrape(testing, driver, headless, my_subjects):
    # Start timing
    print('\n=====================[ SCRAPING ]=====================')
    start_time = time.time()

    slot_scraper = SlotScraper(driver=driver, headless=headless, my_subjects=my_subjects)
    slot_scraper.get_page(testing=testing)

    if not testing:
        slot_scraper.login()
        slot_scraper.enroll()

    # If testing, directly navigate to page
    slot_scraper.check_tnc()
    slot_scraper.scrape()
    slot_scraper.export()

    # End timing
    end_time = time.time()  
    print(f'\nTotal scraping time: {end_time - start_time:.2f}s')
    print('======================================================\n')

if __name__ == '__main__':
    my_subjects = [
        'web fundamentals',
        'operating system fundamentals',
        'information systems analysis & design'
    ]
    start_scrape(testing=True, driver=None, headless=True, my_subjects=my_subjects)

    # Prompt exit
    input('Exit: ')