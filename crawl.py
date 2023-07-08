import re

from datetime import datetime
from os import getenv, makedirs, path
from urllib.parse import parse_qs

from dotenv import load_dotenv
from requests import Session
from selectolax.parser import HTMLParser
from slugify import slugify
from zenlog import log


# Load env variables from `.env`.
load_dotenv()


OUTPUT_DIR = 'output'

KT_URL = 'https://www.kindertic.com'
LOGIN_PATH = '/ca/iniciar-sessio/#login'
IMG_PATH = '/imatge.php?id='

# This is shamelessly hardcoded, I'm a bit lazy today.
PAGES = {
    'travellers_book': ('/control/index.php?pagina=llra&tip=1&curs=820&id=6025', '/control/index.php?pagina=llra&tip=1&curs=665&id=4712'),
    'class_diaries': ('/control/index.php?pagina=llra&tip=2&curs=820&id=6025', '/control/index.php?pagina=llra&tip=2&curs=665&id=4712'),
}

KNOWN_NAMES = ('ares', 'amaya', 'biel', 'tiavana', 'leo', 'mario', 'víctor', 'elisenda', 'greta', 'domenech', 'ferreira', 'einstein', 'pablo',
               'thiago', 'carlota', 'ferran', 'julia', 'juliet', 'inventors', 'inventores', 'heura', 'ariadna', 'guille', 'noa', 'pintores', 'pintors',
               'f.', 'd.', 'camila', 'nit', 'feliz', 'víctor', 'guillem', 'víctor', 'leonardo', 'victor')

class KinderTicCrawler:

    def __init__(self):
        # Init PHP session.
        self.session = Session()
        self.session.get(KT_URL + LOGIN_PATH)

        self.login()
        items = self.list_travellers_book()
        self.download_contents(items)

        log.info('Done.')

    def login(self):
        data = {
            'usernamekt': getenv('KT_USER'),
            'passwd': getenv('KT_PASSWD'),
            'enviar-login': 'Iniciar+sessió'
        }
        response = self.session.post(KT_URL + LOGIN_PATH, data=data)
        root = HTMLParser(response.text)
        username = root.css_first('div.nomusuari label')
        log.info(f'Logged as {username.text()}.')

    def list_travellers_book(self):
        out = []
        for path_type, paths in PAGES.items():
            for path in paths:
                response = self.session.get(KT_URL + path)
                response.encoding = response.apparent_encoding  # Fix encoding, c'mon, it's 2023, still with this?
                root = HTMLParser(response.text)
                table = root.css_first('table.taula')
                for tr in table.css('tr'):
                    if tds := tr.css('td'):
                        title = self.clean_title(tds[1].text().strip())
                        out.append({'type': path_type,
                                    'dt': datetime.strptime(tds[0].text(), '%d/%m/%Y'),
                                    'title': title,
                                    'link': tds[1].css_first('a').attributes['href']})

        return out

    def download_contents(self, items):
        for item in items:

            url = KT_URL + '/control/' + item['link']
            response = self.session.get(url)
            response.encoding = response.apparent_encoding
            root = HTMLParser(response.text)

            # Create dir.
            readable_date = str(item['dt']).split(' ')[0]
            item_folder = f'{readable_date} - {item["title"]}'
            item_folder = item_folder.replace('/', '-')
            destination_path = path.join(OUTPUT_DIR, item['type'], item_folder)
            makedirs(destination_path, exist_ok=True)

            log.info(f'Downloading contents for {item_folder}...')

            # Write description file.
            description = root.css_first('div.descripcio')
            description_path = path.join(destination_path, 'description.txt')
            with open(description_path, 'w') as f:
                f.write(item_folder + '\n\n' + description.text())

            # Download all pictures in highest possible res.
            for i, image in enumerate(root.css('div.imatges img'), start=1):
                params = parse_qs(image.attributes['src'].split('?')[1])
                image_id = params['id'][0]
                img_url = KT_URL + IMG_PATH + image_id

                idx = str(i).zfill(4)
                image_name = f'{readable_date.replace("-", "")}-{idx}-{image_id}.jpg'
                image_path = path.join(destination_path, image_name)

                with open(image_path, 'wb') as f:
                    log.warning(f'Downloading {img_url} to {image_name}...')
                    f.write(self.session.get(img_url).content)

    @staticmethod
    def clean_title(str_in):
        title = str_in.lower().capitalize()
        title = title.replace('´', "'").replace('’', "'")
        title = title.replace('í', 'í')
        title = title.replace('/', '-')

        parts = title.split(' - ')
        parts = [p.capitalize() for p in parts]
        title = ' - '.join(parts)

        words = re.findall(r"[\w']+", title)
        slug_words = slugify(title)
        for name in KNOWN_NAMES:
            if name not in words and name not in slug_words:
                continue

            title = title.replace(name, name.title())

        # Hardcoded fixes, again I'm lazy today.
        title = title.replace('d.', 'D.').replace('f.', 'F.')
        return title


if __name__ == '__main__':
    ktc = KinderTicCrawler()
