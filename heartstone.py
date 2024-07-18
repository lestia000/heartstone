import time
import re
import pymysql
from pymysql import OperationalError, ProgrammingError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.edge.options import Options

edge_options = Options()
edge_options.add_argument("--headless")

characters = ['Druid', 'Hunter', 'Mage', 'Paladin', 'Priest', 'Rogue', 'Shaman', 'Warlock', 'Warrior', 'Demonhunter',
              'Deathknight', 'Neutral']
card_types = ['基本', '普通', '稀有', '史诗', '传说']
conn = pymysql.connect(
    host="",  # Your host
    user="",  # Your username
    password="",  # Your password
    database="",  # Your database
    connect_timeout=300
)
cursor = conn.cursor()


class Card:
    def __init__(self, cname, ename, seriesName, type, rule):
        self.cname = cname
        self.ename = ename
        self.seriesName = seriesName
        self.type = type
        self.rule = rule

    def show(self):
        print(self.cname, self.ename, self.seriesName, self.type, self.rule)

    def getdata(self):
        return self.cname, self.ename, self.seriesName, self.type, self.rule


def getText(obj):
    return obj.get_attribute("textContent")


def insertData(type, cards):
    global conn,cursor
    retries = 3
    retry_delay = 5
    for retry in range(retries):
        try:
            sql = 'show tables like %s'
            cursor.execute(sql, (type,))
            table_existence = cursor.fetchone()
            if not table_existence:
                create_table_sql = """CREATE TABLE `{}`(
                    cname varchar(255),
                    ename varchar(255),
                    seriesName varchar(255),
                    type varchar(255),
                    rule varchar(255)
                )"""
                cursor.execute(create_table_sql.format(type))
                print(f"Table {type} created")
            cursor.executemany(
                f'insert into {type} (cname,ename,seriesName,type,rule) values(%s,%s,%s,%s,%s)',
                cards)
            conn.commit()
            time.sleep(3)
            break
        except (OperationalError, ProgrammingError) as e:
            conn.close()
            conn = pymysql.connect(
                host="",  # Your host
                user="",  # Your username
                password="",  # Your password
                database="",  # Your database
                connect_timeout=300
            )
            cursor = conn.cursor()
        time.sleep(retry_delay)


def slipDown(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        after_height = driver.execute_script("return document.body.scrollHeight")
        if (last_height == after_height):
            break
        last_height = after_height


def getMsg(element):
    return Card(getText(element.find_elements(By.CLASS_NAME, "cname")[0]),
                getText(element.find_elements(By.CLASS_NAME, "ename")[0]),
                re.findall(r'.*?(?=\()', getText(element.find_elements(By.CLASS_NAME, "seriesName")[0]))[0],
                getText(element.find_elements(By.CLASS_NAME, "type")[0]),
                re.sub(r'^', '', getText(element.find_elements(By.CLASS_NAME, "rule")[0])))


def geneUrl(card_type, character):
    return f"https://www.iyingdi.com/web/tools/hearthstone/cards?pagetype=inquire&rarity={card_type}&faction={character}"


if __name__ == "__main__":
    driver = webdriver.Edge(edge_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 600)

    for character in characters:
        for card_type in card_types:
            en_card_types = {
                "基本": "free",
                "普通": "common",
                "稀有": "rare",
                "史诗": "epic",
                "传说": "legendary"
            }
            driver.get(geneUrl(card_type, character))
            time.sleep(2)
            slipDown(driver)
            time.sleep(3)
            elements = driver.find_elements(By.CLASS_NAME, "card")
            cards = []
            print(len(elements))
            for element in elements:
                card = getMsg(element)
                card.show()
                cards.append(card.getdata())
            print(character, card_type)
            insertData(character+"_"+en_card_types[card_type], cards)
    conn.close()
    cursor.close()
    driver.quit()
