# Swiss Newspapers

import os,shutil,time
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup




class SwissNewspapers:
    def __init__(self):
        self.email = os.environ.get('email')
        self.password = os.environ.get('password')
        self.start_driver()
        self.enter_site()
        self.gather_newspapers()
        self.cancelled = False

    # The following method starts the selenium web driver
    def start_driver(self)->None:
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
        })
        chrome_options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=chrome_options)

    # The following method enters the website
    def enter_site(self)->None:
        self.driver.get('https://www.e-newspaperarchives.ch/?a=a&command=ShowAuthenticateUserPage&opa=e%3D-------en-20--1--img-txIN--------0-----&e=-------en-20--1--img-txIN--------0-----')

        while True:
            try:
                t = self.driver.find_element(By.ID,'cookieconfirm')
            except selenium.common.exceptions.ElementNotVisibleException:
                pass
            else:
                t.click()
                break

        item = self.driver.find_element(By.XPATH,'/html/body/div[2]/div/div/div/div[1]/form/input[7]')
        item.click()

        while True:
            if self.driver.current_url == 'https://chlogin.zd.eiam.admin.ch/auth/saml2/broker/':
                break

        email_entry = self.driver.find_element(By.XPATH,'/html/body/div[1]/div[4]/div[1]/form/div[1]/div/eiam-input/label/input')
        email_entry.send_keys(self.email,Keys.ENTER)

        time.sleep(1)
        password_entry = self.driver.find_element(By.XPATH,'/html/body/div[1]/div[4]/div[1]/form/div[1]/div/eiam-input/label/input')
        password_entry.send_keys(self.password)

        wait = input('Waiting...')
        enter =  self.driver.find_element(By.XPATH,'/html/body/div[1]/div[4]/div[1]/form/div[1]/div/div[3]/eiam-button[2]/button/span[2]')
        enter.click()

    # The following method will gather all the newspapers on the archive
    def gather_newspapers(self)->None:
        while self.driver.current_url != 'https://www.e-newspaperarchives.ch/?a=cl&cl=CL1&e=-------en-20--1--img-txIN--------0-----':
            self.driver.get('https://www.e-newspaperarchives.ch/?a=cl&cl=CL1&e=-------en-20--1--img-txIN--------0-----')

        soup = BeautifulSoup(self.driver.page_source,'lxml')
        inputs = [(n['href'],n.text) for n in soup.find_all('a',href=True) if "sp=" in n['href']]
        years = [year.text for year in soup.find_all('span',style=True) if "(" in year.text and ")" in year.text]
        self.newspaper_dictionary = {}

        for i in range(len(inputs)):
            value = f"https://www.e-newspaperarchives.ch{inputs[i][0]}"
            key = inputs[i][1] + " " + years[i]
            self.newspaper_dictionary[key] = value

    # The following method will download a specific newspaper
    def download_newspaper(self,newspaper:str)->None:
        if newspaper in self.newspaper_dictionary:
            os.mkdir(newspaper)
            website = self.newspaper_dictionary[newspaper]
            abbreviation = website.split("sp=")[1].split("&")[0]
            self.driver.get(website)
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            months = [f"https://www.e-newspaperarchives.ch{month['href']}" for month in soup.find_all('a', href=True) if "sp=" in month['href'] and month['href'].count(".") > 1]
            for month in months:
                month_directory = month.split("&sp")[0].split(".")
                month_directory = month_directory[-1] + "-" + month_directory[-2]
                os.mkdir(f"{newspaper}/{month_directory}")
                self.driver.get(month)
                day_soup = BeautifulSoup(self.driver.page_source, 'lxml')
                n = []
                for char in newspaper:
                    if char == "(":
                        n.pop()
                        break
                    else:
                        n.append(char)
                n = "".join(n)
                days = [f"https://www.e-newspaperarchives.ch{day['href']}" for day in day_soup.find_all('a', href=True) if day.text == n]
                for day in days:
                    file_name = day.split("-")[1].split("d&d=")[-1]
                    file_name = file_name.replace(f"{abbreviation}", f"{abbreviation}_")
                    file_name += ".pdf"
                    self.driver.get(day)
                    if self.cancelled == False:
                        cancel_button = self.driver.find_element(By.CSS_SELECTOR,"button.canceltutorial.btn.btn-primary")
                        cancel_button.click()
                        self.cancelled = True
                    pdf_link = self.driver.find_element(By.ID, 'documentstaticpdfdownload')
                    self.driver.get(pdf_link.get_attribute('href'))
                    while True:
                        if file_name in os.listdir("../../Downloads"):
                            print(f"{newspaper}/{file_name} was downloaded.")
                            with open(f"download_results.txt", 'a') as f:
                                f.write(f"{newspaper}/{file_name} was downloaded\n")
                            shutil.move(f"../../Downloads/{file_name}", f"{newspaper}/{month_directory}")
                            break

    # The following method will update a given newspaper
    def update_newspaper(self,newspaper:str)->None:
        if newspaper in self.newspaper_dictionary:
            website = self.newspaper_dictionary[newspaper]
            abbreviation = website.split("sp=")[1].split("&")[0]
            if newspaper not in os.listdir():
                self.download_newspaper(newspaper)
            else:
                self.driver.get(website)
                soup = BeautifulSoup(self.driver.page_source,'lxml')
                months = [f"https://www.e-newspaperarchives.ch{month['href']}" for month in soup.find_all('a', href=True) if "sp=" in month['href'] and month['href'].count(".") >1]
                for month in months:
                    month_directory = month.split("&sp")[0].split(".")
                    month_directory = month_directory[-1] + "-" + month_directory[-2]
                    try:
                        os.mkdir(f"{newspaper}/{month_directory}")
                    except FileExistsError:
                        pass
                    self.driver.get(month)
                    day_soup = BeautifulSoup(self.driver.page_source,'lxml')
                    n = []
                    for char in newspaper:
                        if char == "(":
                            n.pop()
                            break
                        else:
                            n.append(char)
                    n = "".join(n)
                    days = [f"https://www.e-newspaperarchives.ch{day['href']}" for day in day_soup.find_all('a',href=True) if day.text == n]
                    for day in days:
                        file_name = day.split("-")[1].split("d&d=")[-1]
                        file_name = file_name.replace(f"{abbreviation}",f"{abbreviation}_")
                        file_name += ".pdf"
                        if file_name not in os.listdir(f"{newspaper}/{month_directory}"):
                            self.driver.get(day)
                            if self.cancelled == False:
                                cancel_button = self.driver.find_element(By.CSS_SELECTOR,"button.canceltutorial.btn.btn-primary")
                                cancel_button.click()
                                self.cancelled = True
                            pdf_link = self.driver.find_element(By.ID,'documentstaticpdfdownload')
                            self.driver.get(pdf_link.get_attribute('href'))
                            while True:
                                if file_name in os.listdir("../../Downloads"):
                                    print(f"{newspaper}/{file_name} was downloaded.")
                                    with open(f"download_results.txt",'a') as f:
                                        f.write(f"{newspaper}/{file_name} was downloaded\n")
                                    shutil.move(f"../../Downloads/{file_name}",f"{newspaper}/{month_directory}")
                                    break
                        else:
                            print(f"{newspaper}/{file_name} was already downloaded.")
        else:
            print("Newspaper not found")

    # The following method will update all the newspapers on the archive
    def update_all(self):
        for newspaper in self.newspaper_dictionary:
            self.update_newspaper(newspaper)

    # The following method will download all the newspapers on the archive
    def download_all(self):
        for newspaper in self.newspaper_dictionary:
            self.download_newspaper(newspaper)

    # The following method will print all the names of the newspaper
    def print_names(self):
        for n in self.newspaper_dictionary:
            print(n)


if __name__ == "__main__":
    sn = SwissNewspapers()
    sn.download_all()