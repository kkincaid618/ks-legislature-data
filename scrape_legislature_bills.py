from requests import get, exceptions
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, date

class ScrapeKSLegislatureBills():
    def __init__(self):
        self.todays_date = date.today()
        
        self.leg_session = 'li/b2023_24'
        self.base_url = f'http://kslegislature.org/'
        self.ks_bills_url = f'{self.base_url}{self.leg_session}/measures/bills/'

    def _make_request(self, url):
        try:
            r = get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, features='lxml')
        except exceptions.HTTPError as err:
            raise SystemExit(err)

        return soup

    def get_list_of_bills(self):
        url = self.ks_bills_url
        soup = self._make_request(url)

        bill_title_elements = soup.find_all(class_='module-title')
        bill_data = []

        for bill in bill_title_elements:
            link = bill.get('href')
            title = bill.text

            # Identify bill code starting with either SB or HB
            code = re.findall('((?:SB|HB)\d+)\s\-',title)[0]
            code_prefix = code[:2]

            # Identify chamber of origin based on previously identified bill code
            if code_prefix == 'SB':
                chamber_of_origin = 'Senate'
            elif code_prefix == 'HB':
                chamber_of_origin = 'House'
            else:
                chamber_of_origin = ''

            bill_info = [code, chamber_of_origin, title, link]
            bill_data.append(bill_info)

        # Store list of bills into a dataframe, save locally and into self
        df_bills_list = pd.DataFrame(bill_data,columns=['bill_code','chamber_of_origin','title','link'])
        df_bills_list = df_bills_list.set_index('bill_code')

        file_path = f'bill_register_{self.todays_date}.csv'
        df_bills_list.to_csv(file_path)

        self.df_bills_list = df_bills_list
        self.num_bills = len(df_bills_list)

    def _categorize_bill_actions(self, action):
        action_lowercase = action.lower()

        # Regex would probably be a stronger fit here, but this is a sufficient Proof of Concept
        if 'referred' in action_lowercase:
            action_group = 'Referred to Committee'
        elif 'Hearing' in action and 'CANCELED' not in action:
            action_group = 'Hearing'
        elif 'Hearing' in action and 'CANCELED' in action:
            action_group = 'Hearing Canceled'
        elif 'committee report recommending' in action_lowercase:
            action_group = 'Committee Report Submitted'
        elif 'by governor on' in action_lowercase:
            action_group = 'Action Taken by Governor'
        elif 'enrolled and presented to governor' in action_lowercase:
            action_group = 'Awaiting Governor'
        elif 'passed' in action_lowercase and 'final action' in action_lowercase:
            action_group = 'Passed Chamber Vote'
        elif 'substitute bill be passed' in action_lowercase:
            action_group = 'Passed Chamber Vote'
        elif 'Committee of the Whole - Be passed' in action:
            action_group = 'Passed Chamber Vote'
        elif "passed over and retain a place" in action_lowercase:
            action_group = 'Pending Floor Vote or Action'
        elif "general orders" in action_lowercase:
            action_group = 'Pending Floor Vote or Action'
        elif action == 'Introduced':
            action_group = 'Introduced'
        elif action == 'Stricken from Calendar by Rule 1507':
            action_group = 'Stricken from Calendar by Rule 1507'
        elif 'prefiled for introduction' in action_lowercase:
            action_group = 'Prefiled for Introduction'
        elif 'Received and Introduced' in action:
            action_group = 'Pending Floor Vote or Action'
            # Received in 2nd chamber
        elif 'motion to amend' in action_lowercase:
            action_group = 'Motion to Amend'
        elif 'amendment' in action_lowercase and ('was adopted' in action_lowercase or 'passed' in action_lowercase):
            action_group = 'Amendment Adopted'
        elif 'amendment' in action_lowercase and 'was rejected' in action_lowercase:
            action_group = 'Amendment Rejected'
        elif action == 'Committee of the Whole - Committee Report be adopted':
            action_group = 'Committee Report Adopted'
        elif 'engrossed' in action_lowercase:
            action_group = 'Bill Engrossed'
        elif 'amendment was ruled' in action_lowercase:
            action_group = 'Amendment Challenged'
        elif 'withdrawn from committee on' in action_lowercase:
            action_group = 'Withdrawn from Committee'
        elif 'consent calendar passed' in action_lowercase:
            action_group = 'Added to Consent Calendar'
        elif 'to rerefer' in action_lowercase and 'passed' in action_lowercase:
            action_group = 'Motion to Rerefer - Passed'
        elif 'to rerefer' in action_lowercase:
            action_group = 'Motion to Rerefer - Failed'
        elif 'nonconcurred with amendments' in action_lowercase:
            action_group = 'Nonconcurrence with Amendments from Counterpart Chamber'
        else:
            action_group = ''
            print(f'[ALERT] Null Action Group ==> {action}')
        
        return action_group

    def _check_for_votes(self, c):
        hyperlinks = c.find_all('a',href=True)
        
        if len(hyperlinks) > 0: 
            voterlinks = [h for h in hyperlinks if 'vote_view' in h['href']]
            
            if len(voterlinks) == 1:
                link_value = voterlinks[0]['href']
            else:
                link_value = ''
        else:
            link_value = ''       
        
        if 'vote_view' in link_value:
            voting_link = link_value
            is_vote = 1
        else:
            voting_link = None
            is_vote = 0
        
        return voting_link, is_vote
    
    def _get_one_bills_history(self, bill_code, bill_url):
        todays_date = self.todays_date

        # Navigate out to the bill's dedicated page and scrape html
        url_base = self.base_url
        url = f'{url_base}{bill_url}'
        soup = self._make_request(url)
        
        # Isolate the history table and bill description for parsing
        short_desc = soup.find_all(class_='truncated_text')[0].text
        history_tables = soup.find_all(id=re.compile("history-tab"))
        bill_history_list = []

        num_actions = 0
        num_amends = 0
        num_comms = 0
        num_hearings = 0
        num_actions = 0
        hearing_dts = []

        for t in range(len(history_tables)):
            history_table_rows = history_tables[t].find_all('tr')

            for r in history_table_rows:
                c_counter = 1
                history_table_cols = r.find_all('td')

                for c in history_table_cols:
                    if c_counter == 1:
                        date_str = c.text.strip()
                        date =  datetime.strptime(date_str, "%a, %b %d, %Y")
                    elif c_counter == 2:
                        chamber = c.text.strip()
                    elif c_counter == 3:
                        action = " ".join(c.text.split())
                        action_group = self._categorize_bill_actions(action)

                        if action == "Introduced":
                            intro_date = date
                        elif "Motion to Amend" in action:
                            num_amends += 1
                        elif "Referred to Committee" in action:
                            num_comms += 1
                        elif "rerefer" in action or "re-refer" in action:
                            num_comms += 1
                        elif "Hearing" in action:
                            num_hearings += 1
                            hearing_dts.append(date)

                        voting_link, is_vote = self._check_for_votes(c)
                    
                    c_counter += 1
                
                row = [bill_code, short_desc, num_actions, date, chamber, action, action_group, is_vote, voting_link]
                bill_history_list.append(row)

                num_actions += 1

        # Store data in variables for further processing
        bill_meta_list = [bill_code, short_desc, intro_date, num_actions, num_amends, num_comms, num_hearings, hearing_dts]

        df_columns = ['bill_code', 'bill_description', 'row_order_desc', 'date', 'chamber', 'action', 'action_group', 'is_vote','voting_link']
        bill_history_df = pd.DataFrame(bill_history_list, columns = df_columns)

        return bill_meta_list, bill_history_df

    def _date_fields(self):
        df_bill_meta = self.df_bill_meta

        df_bill_meta['refresh_date'] = pd.to_datetime(self.todays_date)
        # print(df_bill_meta.dtypes)
        df_bill_meta['days_from_intro_to_last_action'] = (df_bill_meta['most_recent_action_date'] - df_bill_meta['introduced_date']).dt.days
        df_bill_meta['days_since_last_action'] = (df_bill_meta['refresh_date'] - df_bill_meta['most_recent_action_date']).dt.days
        df_bill_meta['days_since_introduction'] = (df_bill_meta['refresh_date'] - df_bill_meta['introduced_date']).dt.days

        self.df_bill_meta = df_bill_meta

    def _most_recent_action(self):
        all_bill_actions_df = self.all_bill_actions_df
        df_bill_meta = self.df_bill_meta
        
        df_last_action = all_bill_actions_df[all_bill_actions_df['row_order_desc'] == 1][['bill_code','chamber','date','action']]
        df_last_action.columns = ['bill_code','current_chamber','most_recent_action_date','most_recent_action']

        df_bill_meta = df_bill_meta.merge(df_last_action, left_on='bill_code', right_on='bill_code')
        self.df_bill_meta = df_bill_meta

    def _bill_metadata(self, all_bills_meta_list):
        meta_columns = ['bill_code','bill_description','introduced_date','num_leg_actions','num_amends_proposed','num_comms_referred','num_hearings_held','hearing_dts']
        df_bill_meta = pd.DataFrame(all_bills_meta_list, columns=meta_columns)
        
        self.df_bill_meta = df_bill_meta
        self._most_recent_action()
        self._date_fields()

        self.df_bill_meta.to_csv(f'bill_metadata_{self.todays_date}.csv',index=False)

    def get_all_bills_history(self):
        df_bills_list = self.df_bills_list
        num_bills = len(df_bills_list)

        #Initialize empty dataframe to store bill history
        all_bill_actions_df = None
        all_bills_meta_list = []

        # Loop through bills and parse history for each
        for b in range(num_bills):
            bill_code = df_bills_list.index[b]
            bill_url = df_bills_list.iloc[b, 2]

            bill_meta_list, bill_history_df = self._get_one_bills_history(bill_code, bill_url)
            all_bills_meta_list.append(bill_meta_list)

            if all_bill_actions_df is None:
                all_bill_actions_df = bill_history_df
            else:
                all_bill_actions_df = pd.concat([all_bill_actions_df, bill_history_df])

        self.all_bill_actions_df = all_bill_actions_df
        
        self._bill_metadata(all_bills_meta_list)
        
        file_path = f'legislative_actions_{self.todays_date}.csv'
        all_bill_actions_df.to_csv(file_path, index=False)

    def _all_voting_actions(self):
        all_bill_actions_df = self.all_bill_actions_df
        all_voting_actions = all_bill_actions_df[all_bill_actions_df['is_vote'] == 1]

        self.voting_actions = all_voting_actions

    def _vote_group(self, word):

        if word in ('Yea','Nay','Present','Absent'):
            loop_group = word
        elif word == 'Not' and (loop_group == 'Present' or loop_group == 'Absent'):
            loop_group = loop_group
        elif word == 'Not':
            loop_group = word
        else:
            loop_group = loop_group

        return loop_group

    def get_all_voting_records(self):
        self._all_voting_actions()
        voting_actions = self.voting_actions
        num_votes = len(voting_actions)

        bill_votes = []
        
        # Should make indices dynamic
        for v in range(num_votes):
            bill_code = voting_actions.iloc[v, 0]
            vote_date = voting_actions.iloc[v, 1]
            vote_text = voting_actions.iloc[v, 2]
            vote_link = voting_actions.iloc[v, 3]
            vote_chamber = voting_actions.iloc[v, 4]
            vote_type = voting_actions.iloc[v, 5]

            url = f'{self.base_url}{vote_link}'
            soup = self._make_request(url)

            voting_block_html = soup.find_all(id='main_content')[0]
            voting_block_text = voting_block_html.get_text()
            text_list = voting_block_text.split()

            loop_group = None

            i = 0

            while i < len(text_list):            
                word = text_list[i]

                loop_group = self._vote_group(word)

                if loop_group is not None and word[0] != '(' and word != loop_group and word not in ('-','Yea','Nay','Present','Absent','Not', 'and','Passing','Voting'):
                    if len(word) == 2 and word[1:2] == '.':
                        voter = ' '.join([word, text_list[i + 1].replace(',','')])
                        i += 1
                    else:
                        voter = word.replace(',','')

                    if loop_group in ('Yea','Nay','Present'):
                        vote = loop_group
                    elif loop_group == 'Absent':
                        vote = 'Absent and Not Voting'
                    elif loop_group == 'Not':
                        vote = 'Not Voting'
                
                    bill_votes.append([bill_code, vote_chamber, vote_text, vote_type, vote_date, voter, vote, vote_link])

                i += 1

        df_voting_roll = pd.DataFrame(bill_votes, columns=['bill_code','chamber','action', 'vote_type', 'date','representative','vote','voting_info_url'])
        df_voting_roll.to_csv(f'ks_legislative_votes_{self.todays_date}.csv', index=False)

def main():
    data_processor = ScrapeKSLegislatureBills()
    data_processor.get_list_of_bills()
    data_processor.get_all_bills_history()

if __name__ == "__main__":
    main()
