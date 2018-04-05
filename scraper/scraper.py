from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup
import regex as re
import sqlite3
from time import sleep
from env import USERNAME, PASSWORD

def login(driver):
    username = driver.find_element_by_id("username")
    password = driver.find_element_by_id("password")
    log_in = driver.find_element_by_name("_eventId_proceed")

    username.send_keys(USERNAME)
    password.send_keys(PASSWORD)
    log_in.click()

def get_link_set():
    driver = webdriver.Firefox()
    driver.get("https://evaluations.uchicago.edu")
    login(driver)

    driver.implicitly_wait(1)
    department = driver.find_element_by_name("Department")
    year = driver.find_element_by_id("AcademicYear")

    options = department.find_elements_by_tag_name("option")

    for option in options:
        # print(option.get_attribute("value"))
        val = option.get_attribute("value")
        if val == "CMSC":
            option.click()

    years = year.find_elements_by_tag_name("option")
    for yr in years:
        val = yr.get_attribute("value")
        if val == "2015":
            yr.click() 

    driver.find_element_by_id("keywordSubmit").click()

    driver.implicitly_wait(1)
    linkSet = set()
    links = driver.find_elements_by_tag_name("a")
    for link in links:
        href = link.get_attribute("href")
        if "evaluation.php?id=":
            linkSet.add(href)

    driver.close()

    return linkSet

def scrape():
    links = get_link_set()
    driver = webdriver.Firefox()
    first = True
    for link in links:
        print(link)
        driver.get(link)
        if first:
            login(driver)
            first = False
        driver.implicitly_wait(1)
        content = get_source_content(driver)
        print(content)
        if not content:
            continue
        table = get_table(content, "The Instructor")
        print(parse_table(content, "The Instructor"))

        print(get_instructor(content))
        add_eval(content)

        sleep(2)

def get_content(file):
    with open(file) as f:
        html_doc = f.read()

    soup = BeautifulSoup(html_doc, "html.parser")
    content = soup.find("div", {"id": "content"})
    return content

def get_source_content(driver):
    source = driver.page_source
    soup = BeautifulSoup(source, "html.parser")
    content = soup.find("div", {"id": "content"})
    return content

def get_class_info(content):
    title = content.find("h1", {"id": "page-title"})
    if not title:
        return
    split = title.string.split(": ")
    return split[0], split[1]

def get_instructor(content):
    exp = "\<strong\>Instructor\(s\):\<\/strong\> (.+)\<br\/\>"
    paragraphs = content.find_all("p")
    for p in paragraphs:
        p_text = str(p)
        m = re.search(exp, p_text)
        if m:
            return m.group(1)

def get_table(content, title):
    headers = content.find_all("h2")
    for h in headers:
        if h.string == "The Instructor":
            return h.next_sibling.next_sibling
    return None

def get_mean(arr):
    if len(arr) != 6:
        return
    ## remove N/A
    arr = arr[1:]
    mean = 0
    for i in range(len(arr)):
        mean += float(i)/5 * arr[i]
    return int(mean)

def parse_table(content, title):
    table = get_table(content, title)
    data = []
    table_body = table#.find('tbody')

    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        mean = get_mean([int(ele.text.strip()[:-1]) for ele in cols])
        data.append(mean)
    return data[1:]

def initialize_db():
    conn = sqlite3.connect("uchi_evaluations.db")
    conn.text_factory = str
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    """
    Creates tables in the database if they do not already exist.
    returns: None
    """
    cmd = """
            CREATE TABLE instructors (
                instructor_id INTEGER PRIMARY KEY,
                instructor_name TEXT
            );
            CREATE TABLE classes (
                class_id INTEGER PRIMARY KEY,
                instructor_id INT,
                class_name TEXT,
                class_number TEXT,
                FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
            );
            CREATE TABLE instructor_evals (
                instructor_eval_id INTEGER PRIMARY KEY,
                instructor_id INT,
                class_id INT,
                organized INT,
                clear INT,
                interesting INT,
                pos_attitude INT,
                accessible INT,
                recommend INT,
                FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id),
                FOREIGN KEY (class_id) REFERENCES classes(class_id)
            );
            """
    try:
        c.executescript(cmd)
    except sqlite3.OperationalError as err:
        print(err)
    conn.commit()
    conn.close()

def add_eval(content):
    conn = sqlite3.connect("uchi_evaluations.db")
    c = conn.cursor()

    instructor_name = get_instructor(content)
    cmd = """
    INSERT INTO instructors (instructor_name)
    VALUES ('%s')
    """ % instructor_name
    c.execute(cmd)

    cmd = "SELECT last_insert_rowid()"
    c.execute(cmd)
    instructor_id = c.fetchone()[0]

    class_number, class_name = get_class_info(content)
    cmd = """
    INSERT INTO classes (class_name, class_number, instructor_id) 
    VALUES ('%s', '%s', %d)
    """ % (class_name, class_number, instructor_id)
    c.execute(cmd)

    cmd = "SELECT last_insert_rowid()"
    c.execute(cmd)
    class_id = c.fetchone()[0]

    arr = parse_table(content, "The Instructor")
    cmd = """
    INSERT INTO instructor_evals (instructor_id, class_id, organized, clear, interesting, pos_attitude, accessible, recommend)
    VALUES (%d, %d, %d, %d, %d, %d, %d, %d)
    """ % (instructor_id, class_id, arr[0], arr[1], arr[2], arr[3], arr[4], arr[5])
    c.execute(cmd)

    conn.commit()
    conn.close()

def get_all_evals():
    conn = sqlite3.connect("uchi_evaluations.db")
    c = conn.cursor()
    cmd = "SELECT * FROM instructor_evals"
    c.execute(cmd)
    res = c.fetchall()
    conn.commit()
    conn.close()
    return res

if __name__ == '__main__':
    initialize_db()

    # scrape()
    # driver.get("http://www.google.com")


    # content = get_content("eval.html")
    # # header = get_h2(content, "The Instructor")
    # # print(header)

    # table = get_table(content, "The Instructor")
    # print(parse_table(content, "The Instructor"))

    # print(get_instructor(content))

    # add_eval(content)
    evals = get_all_evals()
    for e in evals:
        print(e)

    # heading = table.h2.string
    # print(heading)


# print(content.prettify())