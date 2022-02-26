import requests
import openpyxl
import json
import hashlib
from bs4 import BeautifulSoup
from pymongo import MongoClient


def mongo_connect(host, port, database):
    """ Функция для подключения к БД MongoDB """
    client = MongoClient(host, port)
    db = client[database]
    return db.vacancies


def get_content(url, search_period="", page="", employment="", area=160, text="") -> tuple:
    """ Функиця принимает параметры для создания ссылки. """
    URL = url
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0"}
    params = {"area": area, "employment": employment,
              "search_period": search_period, "text": text, "page": page}

    response = requests.get(URL, headers=HEADERS, params=params)
    soup = BeautifulSoup(response.text, "lxml")
    return soup, response.url


def get_last_page(html) -> int:
    """ Функция которая выводит последнюю цифру из пагинации """
    content = html
    last_page = content.find("div", {
        "class": "pager", "data-qa": "pager-block"}).find_all("a", {"data-qa": "pager-page"})
    return int(last_page[-1].text)


def salary_string_cleaner(dirty_data):
    """ Функция очищает строку и делает корректную выборку """
    string = dirty_data.text.replace("\u202f", "").split(" ")
    if "до" in string:
        salary_min = None
        salary_max = int(string[1])
        salary_currency = string[-1]
    elif "от" in string:
        salary_min = int(string[1])
        salary_max = None
        salary_currency = string[-1]
    else:
        salary_min = int(string[0])
        salary_max = int(string[2])
        salary_currency = string[-1]

    return salary_min, salary_max, salary_currency


def salary_dictionary(min_s, max_s, cur_s) -> dict:
    """ Функция собирает три значения зарплаты в один словарь """
    return {"Minimum wage": min_s, "Maximum wage": max_s, "Currency": cur_s}


def create_data(vacancy_url, title, salary, source_url, data={}) -> dict:
    """ Функция собирает данные в один словарь, проводит сериализацию и возвращает в виде строки"""
    data["_id"] = hashlib.md5(vacancy_url.encode()).hexdigest()
    data["title"] = title
    data["salary"] = salary
    data["vacancy_url"] = vacancy_url
    data["source_url"] = source_url
    return data


def get_salary_request(db, minimum, maximum):
    """ Функция которая выводит данные соответсвующие условиям ЗП """
    return db.find({"$or": [{"salary.Minimum wage": {"$gt": minimum}}, {
        "salary.Maximum wage": {"$gt": maximum}}]})


def pretty_output(record):
    """ Функция которая просто выводит данные в приятном глазу формате """
    return f'Вакансия: \033[1m\033[32m{record["title"]}\033[0m\nСсылка на вакансию: \033[4m\033[3m\033[36m{record["vacancy_url"]}\033[0m\nЗарплата:\n\tМинимум: \033[33m{record["salary"]["Minimum wage"]}\033[0m\n\tМаксимум: \033[33m{record["salary"]["Maximum wage"]}\033[0m\n\tВалюта: {record["salary"]["Currency"]}\n'


if __name__ == "__main__":
    vacancies_db = mongo_connect("127.0.0.1", 27017, "headhunter")
    while True:
        action = input(
            "Что хотите сделать?\n\t1. Собрать новые вакансии.\n\t2. Вывести данные по записанным вакансиям.\n\tQ. чтобы выйти.\n\n>> ")

        if action == "1":
            find_text = input("Введите текст для поиска вакансий: ")
            region = int(input("Укажите регион для поиска вакансий: "))
            period = int(
                input("Укажите период в который была вывешена вакансия: "))
            first_page = get_content(
                "https://hh.kz/search/vacancy", search_period=period, area=region, text=find_text)[0]
            pages = get_last_page(first_page)

            for page in range(0, pages):
                content, source_url = get_content(
                    "https://hh.kz/search/vacancy", period, page, "", region, text=find_text)
                vacancy_tab = content.find_all(
                    "div", {"class": "vacancy-serp-item"})

                for vacancy in vacancy_tab:
                    title = vacancy.find(
                        "a", {"data-qa": "vacancy-serp__vacancy-title"})
                    vacancy_url = title["href"].split("?")[0]
                    salary_dirty_str = vacancy.find_all(
                        "span", {"class": "bloko-header-section-3"})

                    if len(salary_dirty_str) != 1:
                        s_min, s_max, s_cur = salary_string_cleaner(
                            salary_dirty_str[1])
                    else:
                        s_min = s_max = s_cur = None

                    salary = salary_dictionary(s_min, s_max, s_cur)
                    vacancy = create_data(
                        vacancy_url, title.text, salary, source_url)

                    if vacancies_db.find_one({"_id": vacancy["_id"]}):
                        print("EXIST")
                    else:
                        vacancies_db.insert_one(vacancy)
                        print("New record added")
        elif action == "2":
            vacancies = get_salary_request(vacancies_db, int(input(
                "Укажите порог минимальной ЗП: ")), int(input("Укажите порог максимальной ЗП: ")))

            for vacancy in vacancies:
                print(pretty_output(vacancy))
        elif action.upper() == "Q":
            print("Пока~")
            break
        else:
            print("Такого варианта нет.")
