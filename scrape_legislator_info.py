from requests import get, exceptions
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, date

class ScrapeKSLegislatorBios():
    def __init__(self):
        self.todays_date = date.today()
        
        self.leg_session = 'li/b2023_24'
        self.base_url = f'http://kslegislature.org/'
        self.ks_legs_url = f'{self.base_url}{self.leg_session}/members/'
    
    def _make_request(self, url):
        try:
            r = get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, features='lxml')
        except exceptions.HTTPError as err:
            raise SystemExit(err)

        return soup

    def _legislator_chamber(self, url_text):
        if 'rep_' in url_text:
            chamber = 'House'
        elif 'sen_' in url_text:
            chamber = 'Senate'
        else:
            chamber = ''

        return chamber

    def _legislator_name_title(self, html_body):
        rep_name_phrase = html_body.find('h1').text
        rep_name = ' '.join(rep_name_phrase.split()[1:])
        rep_name_split = rep_name.split('-')

        if len(rep_name_split) > 1:
            rep_name = rep_name_split[0].strip()
            spec_role = rep_name_split[1].strip()
        else:
            spec_role = ''

        return rep_name, spec_role
    
    def _legislator_district(self, html_body):
        dist_num = html_body.split('-')[0].strip().replace('District ','')

        return dist_num
    
    def _legislator_party(self, html_body):
        pol_party = html_body.split('-')[1].strip()

        return pol_party
    
    def _legislator_email(self, sidebar_soup):
        all_sidebar_links = sidebar_soup.find_all('a')

        for l in all_sidebar_links:
            href = l['href']

            if 'ks.gov' in href:
                email_address = href.split(':')[1]

        return email_address
    
    def _legislator_phone(self, sidebar_text, pattern='Phone:\s(\d{3}[\s\-]\d{3}\-\d{4})'):
        phone_number = re.findall(pattern, sidebar_text)[0].replace('-','').replace(' ','')

        return phone_number
    
    def _legislator_details(self, legislator_info_soup):
        url_base = self.base_url

        legislator_url_suffix = legislator_info_soup['href'] # '/li/b2023_24/members/rep_alcala_john_1/'
        legislator_url = f'{url_base}{legislator_url_suffix}' # http://kslegislature.org/li/b2023_24/li/b2023_24/members/rep_alcala_john_1/
        name_abbr = ' '.join(legislator_info_soup.text.split()[1:]) # Alcala
        
        # Parse webpage response
        soup = self._make_request(legislator_url)
        body = soup.find(id='main')
        sub_elem = body.find('h2').text
        sidebar_soup = soup.find(id='sidebar')
        sidebar_text = sidebar_soup.get_text()

        # Retrieve key bio details from the webpage response
        rep_name, spec_role = self._legislator_name_title(body)
        chamber = self._legislator_chamber(legislator_url)
        email_address = self._legislator_email(sidebar_soup)
        phone_number = self._legislator_phone(sidebar_text)
        pol_party = self._legislator_party(sub_elem)
        dist_num = self._legislator_district(sub_elem)

        # Retrieve the legislator's legislative experience in KS from the sidebar
        pattern = '(House|Senate):\s*(\d{4}\s*\-\s*.*)'
        leg_exp = re.findall(pattern, sidebar_text)

        all_exp = []

        for entry in leg_exp:
            chamber_exp = entry[0]
            years = ''.join(entry[1].split())
            start_yr = years.split('-')[0]
            end_yr = years.split('-')[1]

            leg_exp_data = [chamber_exp, start_yr, end_yr]
            all_exp.append(leg_exp_data)

        legislator_bio_data = [chamber, rep_name, spec_role, dist_num, pol_party, email_address, phone_number, all_exp, name_abbr, legislator_url]

        return legislator_bio_data


    def get_legislator_list(self):
        all_legs_url = self.ks_legs_url

        soup = self._make_request(all_legs_url)
        legislators = soup.find_all(class_='module-title') # <a class="module-title" href="/li/b2023_24/members/rep_alcala_john_1/">Rep. Alcala</a>
        all_legislator_bios = []

        for l in legislators:
            legislator_bio_data = self._legislator_details(l)
            all_legislator_bios.append(legislator_bio_data)

        col_names = ['chamber','legislator_name','legislator_title','district','party_affiliation','email_address','phone_number','ks_state_legislative_experience', 'legislator_name_abbr','info_url']
        df_legislators = pd.DataFrame(all_legislator_bios, columns=col_names)
        df_legislators.to_csv(f'ks_legislators_{self.todays_date}.csv', index=False)

def main():
    scraper = ScrapeKSLegislatorBios()
    scraper.get_legislator_list()

if __name__ == "__main__":
    main()