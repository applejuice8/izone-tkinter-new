from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from pathlib import Path
import keyring
import time

class SlotSelector:
    def __init__(self, driver, headless):
        if driver:
            self.driver = driver
        else:
            self.driver = self.init_driver(headless)

        self.wait = WebDriverWait(self.driver, 2)
        self.my_subjects = []
        self.my_l_groups = []
        self.my_p_groups = []
        self.my_w_groups = []

    def init_driver(self, headless):
        print('Setting up webdriver...')

        options = Options()
        if headless:
            options.add_argument('--headless')

        # Use Service with WebDriver Manager
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    
    def init_groups(self, subjects, l_groups, p_groups, w_groups):
        self.my_subjects = subjects
        self.my_l_groups = l_groups
        self.my_p_groups = p_groups
        self.my_w_groups = w_groups

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
        self.wait.until(
            EC.element_to_be_clickable((By.ID, 'chk_confirm'))
        ).click()

    def select(self):
        subjects = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'mySubject')))
        
        for subject in subjects:
            name = subject.find_element(By.XPATH, './/label').text

            # Check if its my subject
            index = self.get_subject_index(name)
            if index is not None:
                print(f'Selecting slot for "{name}"...')

                # Expand dropdowns
                self.expand_dd(subject)    

                # Scrape lectures
                radios = subject.find_elements(By.CLASS_NAME, 'panel-body')
                
                for i, radio in enumerate(radios): 
                    # Determine group num
                    group_num = self.get_group_num(i, index)

                    # Click radio button
                    self.click_radio_btn(radio, group_num)

    def click_radio_btn(self, radio, group_num):
        groups = radio.find_elements(By.CLASS_NAME, 'radio')
        for group in groups:

            if group_num in group.text:
                if 'Temporarily Full' in group.text:
                    print('Group full')
                    raise AssertionError

                # Click radio button
                group.find_element(By.XPATH, './/label').click()
                return

    def submit(self):
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()

    # Helper Functions
    def get_subject_index(self, name):
        for i, myS in enumerate(self.my_subjects):
            if myS in name.lower():
                return i
        return None
    
    def expand_dd(self, subject):
        panel_groups = subject.find_elements(By.CLASS_NAME, 'panel-group')
        for panel_group in panel_groups:
            
            # Try expand dropdown
            try:
                panel_group.find_element(By.XPATH, './/span[contains(@class, "glyphicon-chevron-down")]').click()
                time.sleep(0.2)
            except NoSuchElementException:
                pass

    def get_group_num(self, i, index):
        if i == 0:
            group_num = self.my_l_groups[index]
        elif i == 1:
            group_num = self.my_p_groups[index]
        else:
            group_num = self.my_w_groups[index]
        return group_num

def select_slot(driver, testing, headless, subjects, l_groups, p_groups, w_groups):
    # subjects = ['information systems analysis & design', 'operating system fundamentals', 'web fundamentals']
    # l_groups = [' 1 ', ' 1 ', '1']
    # p_groups = [' 2 ', ' 3 ', ' 10 ']
    # w_groups = ['  ', '  ', '  ']

    # Start timing
    print('\n=====================[ SELECTING ]=====================')
    start_time = time.time()

    slot_selector = SlotSelector(driver=driver, headless=headless)
    slot_selector.init_groups(subjects, l_groups, p_groups, w_groups)
    slot_selector.get_page(testing=testing)

    try:
        if not testing:
            slot_selector.login()
            slot_selector.enroll()

        # If testing, directly navigate to page
        slot_selector.check_tnc()

        # Select
        slot_selector.select()
        slot_selector.submit()
    except Exception as e:
        print(e)
        input('Error encountered. Continue manually: ')

    # End timing
    end_time = time.time()  
    print(f'\nTotal select time: {end_time - start_time:.2f}s')
    print('======================================================\n')

if __name__ == '__main__':
    select_slot(
        driver=None,
        testing=True,
        headless=False,
        subjects = ['information systems analysis & design', 'operating system fundamentals', 'web fundamentals'],
        l_groups=[' 1 ', ' 1 ', ' 1 '],
        p_groups=[' 2 ', ' 3 ', ' 10 '],
        w_groups=['  ', '  ', '  ']
    )

    # Prompt exit
    input('Exit: ')