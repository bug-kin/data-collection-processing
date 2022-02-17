import requests
import openpyxl
from bs4 import BeautifulSoup


def get_connect(url, search_period="", page="", employment="", area=160, text=""):
    URL = url
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0"}
    params = {"area": area, "employment": employment,
              "search_period": search_period, "text": text, "page": page}

    response = requests.get(URL, headers=HEADERS, params=params)
    soup = BeautifulSoup(response.text, "lxml")
    return soup, response.url


def create_csv():
    book = openpyxl.Workbook()
    sheet = book.active
    sheet['A1'] = "Наименование вакансии"
    sheet['B1'] = "Минимальная зарплата"
    sheet['C1'] = "Максимальная зарплата"
    sheet['D1'] = "Валюта"
    sheet['E1'] = "Ссылка на вакансию"
    sheet['F1'] = "Ссылка на сайт"
    return book, sheet


def salary_string_cleaner(dirty_data):
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


if __name__ == "__main__":
    find_text = input("Введите текст для поиска вакансий:\t")
    region = int(input("Укажите регион для поиска вакансий:\t"))
    period = int(input("Укажите период в который была вывешена вакансия::\t"))
    pages = int(input("Сколько страниц собрать?\t"))
    row = 2
    book, sheet = create_csv()  # Инициализация CSV файла
    for page in range(0, pages):
        content, page_url = get_connect(
            "https://hh.kz/search/vacancy", period, page, "", region, text=find_text)
        vacancy_tab = content.find_all(
            "div", {"class": "vacancy-serp-item"})
        print(len(vacancy_tab))
        for vacancy in vacancy_tab:
            title = vacancy.find(
                "a", {"data-qa": "vacancy-serp__vacancy-title"})
            print(title)
            salary_dirty_str = vacancy.find_all(
                "span", {"class": "bloko-header-section-3"})
            if len(salary_dirty_str) != 1:
                s_min, s_max, s_cur = salary_string_cleaner(
                    salary_dirty_str[1])
            else:
                s_min = s_max = s_cur = "-"

            sheet[f'A{row}'] = title.text
            sheet[f'B{row}'] = s_min
            sheet[f'C{row}'] = s_max
            sheet[f'D{row}'] = s_cur
            sheet[f'E{row}'] = title["href"]
            sheet[f'F{row}'] = page_url
            row += 1

    book.save('hh.csv')
    book.close()
