import requests
from bs4 import BeautifulSoup
import pandas as pd


data = []


base_url = "https://medlineplus.gov/ency/encyclopedia_{}.htm"
letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


desired_headers = ['Symptoms', 'Treatment', 'Causes', 'Prevention', 'Possible Complications', 'Exams and Tests',
                   'How the test is performed', 'How to Prepare for the Test', 'Why the Test is Performed',
                   'Risks', 'Alternative Names', 'Normal Results']


for letter in letters:

    url = base_url.format(letter)
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve data for letter: {letter}")
        continue


    soup = BeautifulSoup(response.content, "html.parser")


    ul_index = soup.find('ul', id='index')
    if not ul_index:
        print(f"No terms found for letter: {letter}")
        continue


    terms = ul_index.find_all('li')


    for term in terms:
        link = term.find('a')
        if link:
            term_name = link.text.strip()
            term_link = "https://medlineplus.gov/ency/" + link['href']


            term_response = requests.get(term_link)
            term_soup = BeautifulSoup(term_response.content, "html.parser")


            summary_div = term_soup.find('div', id='ency_summary')
            summary_texts = []
            if summary_div:
                paragraphs = summary_div.find_all('p')
                summary_texts.extend(p.get_text(strip=True) for p in paragraphs)

                list_items = summary_div.find_all('li')
                summary_texts.extend(li.get_text(strip=True) for li in list_items)


            sections = term_soup.find_all('section')
            section_texts = []
            for section in sections:
                header_div = section.find('div', class_='section-header')
                if header_div:
                    header_title = header_div.find('h2')
                    if header_title and header_title.get_text(strip=True) in desired_headers:
                        section_title = header_title.get_text(strip=True)
                        section_texts.append(f"Section Title: {section_title}")

                        paragraphs = section.find_all('p')
                        section_texts.extend(p.get_text(strip=True) for p in paragraphs)

                        list_items = section.find_all('li')
                        section_texts.extend(li.get_text(strip=True) for li in list_items)


            explanation = "\n".join(summary_texts + section_texts)


            data.append([term_name, term_link, explanation])


df = pd.DataFrame(data, columns=['Medical Term', 'Link to Article', 'Explanation'])


print(df)


df.to_csv("medlineplus_medical_terms.csv", index=False)
