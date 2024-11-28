from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from pytempmail import TempMail
import time, requests, os
from pyvirtualdisplay import Display
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import pandas as pd
from huggingface_hub import HfApi
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Start a virtual display
display = Display(visible=0, size=(1920, 1080))
display.start()

postgres_engine = create_engine(os.getenv('POSTGRES_URL'), poolclass=NullPool)

tm=TempMail()
email = tm.email

username = f"{email.split("@")[0].replace(".","")}{int(time.time())}"

def wait_for_element(driver, xpath, waitS = 100):
    for i in range(waitS):
        if len(driver.find_elements(By.XPATH, xpath)) > 0:
            break
        time.sleep(1)
    else:
        raise Exception(f"Unable to locate element : {xpath}")

options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_extension("capsolver.crx")

driver = webdriver.Chrome(options)
driver.maximize_window()
driver.get("chrome-extension://hlifkpholllijblknnmbfagnkjneagid/popup/popup.html")
print(driver.title)
driver.get("https://huggingface.co/join")
print("Home Page loaded")
wait_for_element(driver, "//input[@name='email']")
driver.find_element(By.XPATH, "//input[@name='email']").send_keys(email)
driver.find_element(By.XPATH, "//input[@name='password']").send_keys(os.getenv("PASSWORD"))
wait_for_element(driver, "//input[@name='password']")
driver.find_element(By.XPATH, "//input[@name='password']").submit()
print("Filled email and pass and submit")
wait_for_element(driver, "//input[@name='username']")
driver.find_element(By.XPATH, "//input[@name='username']").send_keys(username)
driver.find_element(By.XPATH, "//input[@name='fullname']").send_keys("IMDB")
driver.find_element(By.XPATH, "//input[@type='checkbox']").click()
wait_for_element(driver, "//button[@type='submit']")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
driver.find_element(By.XPATH, "//button[text()='Skip']").click()
print("Waiting for email", email, username)

conf_url = None
while True:
    inbox=tm.get_mails()
    if inbox:
        for x in inbox[:5]:
            if 'huggingface' in x.text:
                conf_url = x.text.split("\n")[4].split("\n")[0]
                break
        if conf_url:
            break
    else:
        time.sleep(1)
print(conf_url)
res = requests.get(conf_url)
driver.get("https://huggingface.co/settings/tokens")
driver.find_element(By.XPATH, "//form[@action='/settings/tokens/new']").click()
wait_for_element(driver, "//input[@name='displayName']")
driver.find_element(By.XPATH, "//input[@name='displayName']").send_keys("imdb")
driver.find_element(By.XPATH, "(//div[@class='flex flex-col gap-2']//input[@value='repo.write'])[1]").click()
create_token_ele = driver.find_element(By.XPATH, "//button[text()='Create token']")
actions = ActionChains(driver)
actions.move_to_element(create_token_ele).perform()
create_token_ele.click()
print("Create token clicked")
wait_for_element(driver, "//div[@class='flex gap-2 max-sm:flex-col']/input")
el = driver.find_element(By.XPATH, "//div[@class='flex gap-2 max-sm:flex-col']/input")
hf_token = el.get_attribute("value")
data = {"email" : email, "username" : username, "hf_token" : hf_token, 'time' : str(int(time.time()))}
df = pd.DataFrame([data])

driver.quit()
print(data)

files = ["Dockerfile",]

#for idx, row in df.iterrows():
def create_repos(token, username, n_repos=1):
    # API instance
    api = HfApi(token=token)
    repo_id = username+"/{}"
    repo_type = "space"
    lst = []
    for i in range(n_repos):
        repo_id_n = repo_id.format(f"{int(time.time())}")
        try:
            api.create_repo(repo_id=repo_id_n, repo_type='space', space_sdk='docker',
                            space_secrets=[{"key" : "token", "value" : os.getenv("GHP_TOKEN")},],
                            space_variables=[{"key" : "package", "value" : "qbittorrent-nox"},])
            for file in files:
                #retry 3 times
                for i in range(3):
                    try:
                        api.upload_file(path_or_fileobj=file, path_in_repo=file.split("/")[-1], repo_id=repo_id_n, repo_type=repo_type,)
                        break
                    except:
                        pass
                else:
                    api.delete_repo(repo_id=repo_id_n,repo_type='space',missing_ok=True)
                    raise Exception(f"Could not upload file in {repo_id_n}")
        except Exception as e:
            print(f"Caught Exception at loop : {i}", e)
            break
        data = {}
        data["username"] = username
        data['repo_id'] = repo_id_n
        data['repo_type'] = repo_type
        lst.append(data)
    return lst

lst = create_repos(hf_token, username)
time.sleep(60)
while True:    
    status_code_200 = []
    for x in lst:
        url = f"https://{x['repo_id'].replace("/", "-")}.hf.space"
        status_code_200.append(requests.get(url).status_code == 200)
    if all(status_code_200):
        print("All Repo_running....")
        break
pd.DataFrame(lst).to_sql('hfrepos', postgres_engine, if_exists='append', index=False)
df.to_sql(name='hfaccounts', con=postgres_engine, if_exists='append', index=False)
