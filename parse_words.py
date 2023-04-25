from bs4 import BeautifulSoup
import requests
request = requests.get('https://www.vocabulary.com/lists/187039')
parsed_html = BeautifulSoup(request.text, 'html.parser')
content = parsed_html.find('ol', attrs={'id':'wordlist'})
wordlist = content.find_all('a');

with open('wordlist.txt', 'w+') as wd:
    for el in wordlist:
        wd.write(el.text)
        wd.write("\n")