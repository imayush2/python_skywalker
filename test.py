import sys
import os
import re
import time
import random
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine


download_dir_for_xml_files = r"/Users/ayushgupta/Desktop/Python/who/Application/XML_Files" # Enter Folder path where all the xml files will be downloaded
download_dir_for_excel_files = r"/Users/ayushgupta/Desktop/Python/who/Application/Database" # Enter Folder path where all EXCEL files will be downloaded

# Fetch the disease title from the command-line argument
if len(sys.argv) < 2:
    print("Error: No disease title provided.")
    sys.exit(1)

title = sys.argv[1]  # The title is passed as the first argument to the script

# Example: If you want to print the title to confirm
print(f"Running scraping for: {title}")


# title = "Liver Cancer" # Enter the Disease to search
countries = ["Argentina"] # Enter Countries
whotrialsearch = "https://trialsearch.who.int/"
pubmedsearch = "https://pubmed.ncbi.nlm.nih.gov/" 
google = "https://www.google.com/"

def initialize_driver():
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_dir_for_xml_files,  # Custom download folder
        "download.prompt_for_download": False,        # Don't prompt, just download
        "download.directory_upgrade": True,           # Overwrite files without asking
        "safebrowsing.enabled": True                  # Enable safe browsing
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # chrome_options.add_argument('--headless')  # Run in headless mode
    # chrome_options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration (optional)
    # chrome_options.add_argument('--window-size=1920x1080')  # Set the window size to avoid issues with some websites
    # chrome_options.add_argument('--no-sandbox') 
    # chrome_options.add_argument('--disable-software-rasterizer')

    driver = webdriver.Chrome(options=chrome_options)

    return driver

initial_count = None

def check_for_new_files(download_dir, file_extension=".xml", timeout=30, initial_count=None, wait_time=5):
    
    if initial_count is None:
        initial_count = len([f for f in os.listdir(download_dir) if f.endswith(file_extension)])

    # Wait for the files to download (for example, wait 5 seconds after triggering download)
    time.sleep(wait_time)
    
    # Get the current count of files
    current_count = len([f for f in os.listdir(download_dir) if f.endswith(file_extension)])

    # Check if the file count has increased
    if current_count > initial_count:
        return True
    else:
        return False
    
def get_latest_file(download_dir, file_extension=".xml"):
    # List all files with the specified extension in the directory
    files = [f for f in os.listdir(download_dir) if f.endswith(file_extension)]
    
    if not files:  # If no files found, return None
        return None
    
    # Get the full path for each file and its last modification time
    files_with_times = [(f, os.path.getmtime(os.path.join(download_dir, f))) for f in files]
    
    # Sort files by modification time in descending order (latest file first)
    latest_file = max(files_with_times, key=lambda x: x[1])
    
    return latest_file[0]  

def run_scraping_who(title, countries):
    driver = initialize_driver()
    driver.get(whotrialsearch)
    wait = WebDriverWait(driver, 10)

    # Go to the Advanced Search Page
    advance_search = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Menu1n1"]/table/tbody/tr/td/a')))
    advance_search.click()
    time.sleep(2)

    # Enter search item
    search_input_title = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_txtTitle"]')))
    search_input_title.send_keys(title)
    time.sleep(1)

    # Add countries
    if len(countries)>0:
        for country in countries:
            country_search = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_txtFreeCountry"]')))
            country_search.send_keys(country)
            time.sleep(1)
            country_submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_butAdd"]')))
            country_submit.click()
            time.sleep(1)

    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_btnSearch"]')))
    search_btn.click()
    time.sleep(2)

    # Click to download XML data
    xml_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_btnLaunchDialogTerms"]')))
    xml_btn.click()
    time.sleep(2)

    agree_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_btnExport"]')))
    agree_btn.click()
    time.sleep(2)

    export_all_trials = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_ucExportDefault_butExportAllTrials"]')))
    export_all_trials.click()
    time.sleep(4)

    if check_for_new_files(download_dir_for_xml_files, file_extension='xml', timeout=30, initial_count=initial_count, wait_time=5):
        driver.close()
    else:
        time.sleep(30)
        if check_for_new_files(download_dir_for_xml_files, file_extension='xml', timeout=30, initial_count=initial_count, wait_time=5):
            driver.close()

    return title

def read_latest_xml_file(download_dir):

    data = []
    # Get the latest file in the directory
    latest_file = get_latest_file(download_dir, file_extension=".xml")
    
    if not latest_file:  # If no file is found, return a message
        print("No XML file found.")
        return
    
    # Get the full path of the latest file
    latest_file_path = os.path.join(download_dir, latest_file)

    tree = ET.parse(latest_file_path)
    root = tree.getroot()

    for elem in root.findall('.//'):
        # Extract data
        export_date = elem.find('Export_date').text if elem.find('Export_date') is not None else ''
        trial_id = elem.find('TrialID').text if elem.find('TrialID') is not None else ''
        last_refreshed = elem.find('Last_Refreshed_on').text if elem.find('Last_Refreshed_on') is not None else ''
        public_title = elem.find('Public_title').text if elem.find('Public_title') is not None else ''
        primary_sponsor = elem.find('Primary_sponsor').text if elem.find('Primary_sponsor') is not None else ''
        web_address = elem.find('web_address').text if elem.find('web_address') is not None else ''
        recruitment_status = elem.find('Recruitment_Status').text if elem.find('Recruitment_Status') is not None else ''
        countries = elem.find('Countries').text if elem.find('Countries') is not None else ''
        contact_firstname = elem.find('Contact_Firstname').text if elem.find('Contact_Firstname') is not None else ''
        contact_lastname = elem.find('Contact_Lastname').text if elem.find('Contact_Lastname') is not None else ''
        contact_address = elem.find('Contact_Address').text if elem.find('Contact_Address') is not None else ''
        contact_email = elem.find('Contact_Email').text if elem.find('Contact_Email') is not None else ''
        contact_tel = elem.find('Contact_Tel').text if elem.find('Contact_Tel') is not None else ''
        Contact_Affiliation = elem.find('Contact_Affiliation').text if elem.find('Contact_Affiliation') is not None else ''
        # Append data to the list
        
        data.append({
            'Source': 'WHO International Trial Registry Platform',
            'Data Export Date': export_date,
            'Trial ID': trial_id,
            'Last Refreshed On': last_refreshed,
            'Public Title': public_title,
            'Primary Sponsor': primary_sponsor,
            'Web Address' : web_address,
            'Recruitment Status' :recruitment_status,
            'Countries': countries,
            'Contact Firstname': contact_firstname,
            'Contact Lastname': contact_lastname,
            'Contact Address': contact_address,
            'Contact Email': contact_email,
            'Contact Tel': contact_tel,
            'Affiliation': Contact_Affiliation
        })

    time.sleep(2)
    global df
    # Convert data to DataFrame
    df = pd.DataFrame(data)

    return df   

def process_df(df):
    df = df[df['Last Refreshed On'] != '']
    df = df[df['Last Refreshed On'] != '']
    df['Contact Firstname'] = df['Contact Firstname'].apply(lambda x: str(x).strip())
    df['Contact Lastname'] = df['Contact Lastname'].apply(lambda x: str(x).strip())                                                                   
    df['Full Name'] = df['Contact Firstname'].astype(str) +' '+ df['Contact Lastname'].astype(str)
    df['Full Name'] = df['Full Name'].apply(lambda x: str(x).split(',')[0].replace(';','').replace('nan','').replace('\n',' ').strip()) 
    df['Contact Address'] = df['Contact Address'].apply(lambda x: str(x).replace(';','').replace('nan','').strip())
    df['Contact Email'] = df['Contact Email'].apply(lambda x: str(x).replace(';','').replace('nan','').strip())
    df['Contact Tel'] = df['Contact Tel'].apply(lambda x: str(x).replace(';','').replace('nan','').strip())
    df['Affiliation'] = df['Affiliation'].apply(lambda x: str(x).replace(';','').replace('nan','').strip())
    df = df.drop(columns=['Contact Firstname', 'Contact Lastname'])
    df['Disease Title Searched'] = title   
    df['PubMed Total Results'] = ''
    df['Google Search Key'] = df['Full Name'].astype(str) + '+' +df['Contact Email'].astype(str)
    df['Social Media Links'] = ''
    

    new_order = ['Source','Disease Title Searched','Data Export Date','Trial ID','Affiliation',
             'Full Name', 'Contact Email','Contact Tel','Contact Address',
             'Countries','Primary Sponsor','Public Title', 'Last Refreshed On', 
             'Web Address', 'Recruitment Status', 'PubMed Total Results','Google Search Key','Social Media Links']
            
            
    df = df[new_order]
    return df
            
def run_scraping_pubmed(df):
    driver = initialize_driver()
    # driver = webdriver.Chrome()
    driver.get(pubmedsearch)
    wait = WebDriverWait(driver, 10)

    for index, row in df.iterrows():
        person_name = row['Full Name']
        WebDriverWait(driver, 45).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        WebDriverWait(driver, 45).until(EC.visibility_of_element_located((By.XPATH,'//*[@id="id_term"]')))
        search_box = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="id_term"]')))
        search_box.click()
        search_box.clear()

        time.sleep(1)
        search_box = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="id_term"]')))
        driver.execute_script("arguments[0].value = '';", search_box)

        search_box = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="id_term"]')))
        search_box.send_keys(person_name)
        time.sleep(1)

        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-form"]/div/div[1]/div/button')))
        submit_btn.click()

        WebDriverWait(driver, 30).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

        try:
            wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-results"]/div[2]/div[1]/div[1]/h3/span')))
            last_5_years_filter = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="static-filters-form"]/div/div[1]/div[1]/ul/li[2]/label')))
            last_5_years_filter.click()
            time.sleep(1)
            total_results = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-results"]/div[2]/div[1]/div[1]/h3/span')))
            result_count = total_results.text
            
        except Exception as e:
                try: 
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="article-top-actions-bar"]/div/div/div[1]/span')))
                    result_count = '1'

                except Exception as e:
                    result_count = 'No Result Found'  

        
        
        # display_option = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-form"]/div[2]/div/div[3]/div[2]/button')))
        # display_option.click()
        # format = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="id_format"]')))
        # select = Select(format)
        # select.select_by_visible_text("PubMed")
        df.at[index,'PubMed Total Results'] = result_count

    return df
        
# Function to extract social media links
def find_social_media_links(page_source):
    social_media_patterns = [
        r"(?i)(facebook\.com|https://x\.com|instagram\.com|linkedin\.com|tiktok\.com|pinterest\.com)"
    ]
    
    social_links = []
    
    # Extract all links from the page
    links = re.findall(r'href=["\'](https?://[^\s]+)["\']', page_source)
    for link in links:
        for pattern in social_media_patterns:
            if re.search(pattern, link):
                social_links.append(link)
                break  # Stop after finding one social media platform in the link

    
    return social_links

# Function to search Google using Selenium

def google_search(df):
    driver = webdriver.Chrome()
    driver.get(google)
    wait = WebDriverWait(driver, 10)
    wait_2 = WebDriverWait(driver,300)

    for index, row in df.iterrows():
        try:
            query = row['Google Search Key']

            random_seconds = random.randint(1, 5)  # Random number between 1 and 5 (inclusive)
            time.sleep(random_seconds)
            
            search_box = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="APjFqb"]')))
            search_box.clear()

            search_box = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="APjFqb"]')))
            driver.execute_script("arguments[0].value = '';", search_box)

            search_box = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="APjFqb"]')))
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)  # Press Enter to start search
        
        except Exception as e:
            print(f"Error processing query {query}: {e}")
            continue

        try:
            WebDriverWait(driver, 30).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

            if "www.google.com/sorry/index?" in driver.current_url:
                print(f"Captcha encountered for query: {query}")
                wait_2.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="APjFqb"]')))
            
            random_seconds = random.randint(1, 4)  # Random number between 1 and 4 (inclusive)
            time.sleep(random_seconds)
    
            WebDriverWait(driver, 30).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            pg_source = driver.page_source
            time.sleep(1)

            social_media_links = find_social_media_links(pg_source)
            df.at[index,'Social Media Links'] = social_media_links
        
            pg_source = driver.page_source
            social_media_links = find_social_media_links(pg_source)
            df.at[index, 'Social Media Links'] = social_media_links

            time.sleep(2)  # Rate limiting

        except Exception as e:
            print(f"Error processing query {query}: {e}")
            continue

    driver.quit()
    return


# not to be used in live production 
# this save file locally
# def save_database(df):
#     df = df.drop(columns=['Google Search Key'])
#     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#     db_name = f"{title}_results_{timestamp}.csv"
#     df.to_csv(download_dir_for_excel_files+"\\"+db_name, index=False)
#     print("File Saved. Please review. Thank you.")


#### Calling all functions

print("Running Search on WHO....")
run_scraping_who(title, countries)

print("Reading XML file....")
df = read_latest_xml_file(download_dir_for_xml_files)

df = process_df(df)

print("Running Scrappring on Pubmed....")
df = run_scraping_pubmed(df)

print("Running Google Search....")
google_search(df)

# print("Saving file....")
# save_database(df)

# print("Saving file....")
# save_database_to_mysql(df)

df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# engine = create_engine('mysql+pymysql://root:8287447641@localhost/scraping_db')

# Define your connection credentials
DB_HOST = "db-mysql-nyc3-25722-do-user-20057036-0.k.db.ondigitalocean.com"
DB_USER = "doadmin"
DB_PASSWORD = "AVNS_z5bCFvsK26ykHIDsP2r"
DB_NAME = "defaultdb"
DB_PORT = "25060"

# Create a connection string without SSL parameters
connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connect to the database and push the data
engine = create_engine(connection_string)

# Insert all rows from the DataFrame into the 'users' table (or your table name)
df.to_sql('data', engine, if_exists='append', index=False)

print("Data inserted successfully.")
