# Scraping Data from the Kansas State Legislature
## Purpose

Democracy works best when each consituent participates in the political process. Even so, engaging in the process can be frustrating.  We often hear about what our legislators are doing after it is already done, or our attempts to engage feel fruitless. As Kansans, our representatives in the U.S. House of Representatives represent approximately 735k people. Our senators represent the full state population of ~2.9MM people. This is 30-40 times the number of people represented by our representatives in the KS legislature.

There are many reasons to engage more directly with state representatives than with our federal ones. Federal politicians often start in state government, cases that reach the Supreme Court often regard state legislation, state legislation often informs federal legislation.

Engaging in the process, even at the state level, is easier said than done. The Kansas legislature does a phenomenal job posting daily legislative agendas and generally keeping the public up-to-date on the latest. However, it can still be difficult to interpret and information can be hard to consolidate.

As an analyst and as a citizen, it was important to me to enhance the accessibility of this information in my home state. This meant a few different things:
* Creating data tables that consolidate information from various places on the KS Legislature website
* Creating visualizations that could highlight fast moving legislation consituents should be aware of
* Facilitating analysis of legislative efficiency and shining a brighter light on our representatives. This was especially important to me in regards to voting records which are not consolidated on the legislature website.

## Data Scraper: scrape_legislature_bills.py
-------------------------------

**get_list_of_bills** 

Produces register of all bills for this legislative session of the KS Legislature. The legislative session is currently fixed to 23-24 but future iterations will make this dynamic.

URL Used: ```'http://kslegislature.org/li/b2023_24/measures/bills/'```

| Column        | Type        | Description | Sample(s) |
| ------------- |-------------| ----------- | --------- |
| bill_code     | string      | Short name for the bill in question | 'SB314', 'HB2003'  |
| chamber       | string      | The legislative chamber that originated this bill. This is based on the bill prefix of either 'SB' or 'HB' | 'Senate', 'House' |
| title         | string      | The bill's written title | 'SB314 - Prohibiting the secretary of health and environment from requiring COVID-19 vaccination for children attending a child care facility or school.' |
| bill_link          | string      | The url suffix to navigate to this bill's detail page | '/li/b2023_24/measures/sb314/'|
| refresh_date  | date        | The date that this data was scraped | 2023-03-17|

**get_all_bills_history**

Produces two separate CSV tables of each bill and its history during the session.

The first table is a detailed history table showing each bill and every action taken upon it.

URL Used: ```f'http://kslegislature.org/{bill_link}'```

| Column        | Type        | Description | Sample(s)|
| ------------- |-------------| ------------|----------|
| bill_code     | string | Short name for the bill in question | 'SB314', 'HB2003'|
| bill_description | string | Summary description of the contents of the bill |'Prohibiting the secretary of health and environment from requiring COVID-19 vaccination for children attending a child care facility or school.'|
| row_order | int | The order in which legislative actions took place. The lower the number, the more recent the action. | 0, 1, 2 |
| date  | date | The date in which the legislative action took place. Some dates may be in the future if they are scheduled actions, like hearings. | 2023-03-22 |
| chamber | string | The legislative chamber taking the action. May be different than the chamber that originated the bill. | 'Senate' |
| action  | string | The legislative action that has taken or will take place | 'Hearing: Wednesday, March 22, 2023, 8:30 AM Room 142-S'|
| action_group  | string | A calculated field grouping various legislative actions into buckets | 'Hearing' |
| is_vote | bit | Specifies whether the legislative action included a vote. 0 = Not a vote; 1 = Is a vote | 0, 1 |
| voting_link | string | The link suffix to navigate to the voting roll for this particular vote | '/li/b2023_24/measures/vote_view/je_20230309121706_623750/'|
| refresh_date  | date        | The date that this data was scraped | 2023-03-17 |

The second table is an aggregated view of a bill and its history. It has a single line per bill with aggregate data. *This table is a work in progress.*

| Column        | Type        | Description | Sample(s)|
| ------------- |-------------| ------------|----------|
| bill_code     | string | Short name for the bill in question | 'SB314', 'HB2003'|
| bill_description | string | Summary description of the contents of the bill |'Prohibiting the secretary of health and environment from requiring COVID-19 vaccination for children attending a child care facility or school.'| 
| introduced_date | date | Date that this bill was introduced (not pre-filed) | 2023-03-15 |
| num_leg_actions | int | The total number of actions taken on this bill. Should match the number of rows in the detailed history table | 3 |
| num_amends_proposed | int | The total number of amendments offered to this bill | 0 | 
| num_comms_referred | int | The number of times the bill was referred to committee | 1
| num_hearings_held | int | The number of hearings held or scheduled for this bill | 1 | 
| hearing_dts | list | A list of dates hearings were held (WIP) | [datetime.datetime(2023, 3, 22, 0, 0)] | 
| current_chamber | string | The chamber in which this bill currently sits | 'Senate' | 
| most_recent_action_date | date | The date that the most recent action occurred on this specific bill (WIP) | 2023-03-16 |
| most_recent_action | string | The details for the action that took place most recently for this bill (WIP) | 'Rereferred to Committee on Public Health and Welfare' |
| refresh_date | date | The date that this data was scraped | 2023-03-17 | 
| days_from_intro_to_last_action | int | The number of days that elapsed between the introduction date and the most recent action taken | 1 | 
| days_since_last_action | int | The number of days that elapsed between the most recent action taken ann the refresh date | 1 | 
| days_since_introduction | int | The number of days that elapsed between the introduction date and the refresh date | 2 | 

**get_all_voting_records**

Produces CSV table of all votes for which there is a record. This includes votes on amendments, final actions, etc.

URL Used: ```f'http://kslegislature.org/{voting_link}'```

| Column        | Type        | Description | Sample(s)|
| ------------- |-------------| ------------|----------|
| bill_code | string | Short name for the bill in question | 'SB314', 'HB2003'|
| chamber | string | The legislative chamber voting on the motion. May be different than the chamber that originated the bill. | 'Senate' |
| action | string | The legislative action that has taken place | 'Emergency Final Action - Passed; Yea: 114 Nay: 7'|
| vote_type | string | The type of vote that took place: Final Action, Consent Calendar, etc. | 'Final Action' |
| date | date | Date that the vote occurred | 2023-03-09 |
| representative | string | The legislator participating in the vote. Generally last name only, sometimes includes first initial. | 'Alcala' |
| vote | string | string | The vote this legislator took on this action. Includes non-votes like 'Present' | 'Yea', 'Nay', 'Present but not Voting', 'Absent and not Voting', 'Not Voting' |
| vote_result | string | The final result of the vote | 'Passed', 'Failed' |
| voting_link | string | The link suffix to navigate to the voting roll for this particular vote | '/li/b2023_24/measures/vote_view/je_20230309121706_623750/' |
| refresh_date| date | The date that this data was scraped | 2023-03-17

## Data Scraper: scrape_legislator_info.py
-------------------------------
**get_legislator_list** 

Produces CSV list of all legislators active during this session of the KS Legislature. Includes contact information and other biographical details.

URL Used: ```'http://kslegislature.org/li/b2023_24/members/'```

| Column        | Type        | Description | Sample(s) |
| ------------- |-------------| ----------- | --------- |
| chamber | string | The chamber this individual is a member of | 'Senate', 'House' |
| legislator_name | string | The name of the legislator | 'John Alcala' |
| legislator_title | string | Any special title or position this individual has in the legislature. NULL if not applicable | 'Senate Majority Leader' |
| district | int | The numbered congressional district this legislator represents. Numbers are unique within a chamber, but may be duplicated across chambers | 57 |
| party_affiliation | string | The name of the party the individual is affiliated with. Independents will show as 'Independent' | 'Democrat' |
| email_address | string | Official KS Legislator Email Address | 'John.Alcala@house.ks.gov' |
| phone_number | string | Official KS Legislator Phone Number | '7852967371' |
| ks_state_legislature_experience | list | List of experiences within the KS Legislature (WIP) | [['Senate', '2017', 'Present'], ['House', '2015', '2016'], ['House', '2011', '2012']] |
| legislator_name_abbr | string | Shortened name used in voting rolls. Usually last name only but may include first initial to avoid ambiguity | 'Alcala' |
| info_url | string | The url suffix that contains the legislator's page on the legislature website containing biographical details | '/li/b2023_24/members/rep_alcala_john_1/' |

## Limitations
-------------------------------
* Limited to Current Legislative session. This can be updated in the __init__ for the different classes but is not currently setup to be dynamic.
* These classes are still being tested and QA'ed
* Results are currently stored to CSVs
* No parameters for choosing which outputs to generate and which to skip

## Next Steps for Development
-------------------------------
* Make legislative session dynamic
* Change output from CSV to dataframe or database
* Add legislative calendar to measure what percent done the current session is
* Include bill sponsorship details
* Include minutes & testimony links
* Create parameters to make classes more flexible in regard to which outputs to generate
* Parse legislator experience to develop metrics related to years of experience, number of terms, etc.
* Parse legislative process PDF to display key terms and rules easily
* Stash legislator headshots for use in visualization tools
* Create plotly app to visualize data and enable self-guided analysis

## Instructions for Use
-------------------------------
* Copy Web Scrapers into your project repo
* From terminal, ```cd``` into your project repo
* ```python scrape_legislature_bills.py```

## KS Legislature Specific Resources for Context
-------------------------------
* KS Legislative Procedure: http://www.kslegislature.org/li/s/pdf/kansas_legislative_procedure.pdf
* House Rules: http://www.kslegislature.org/li/s/pdf/house_rules.pdf
* Senate Rules: http://www.kslegislature.org/li/s/pdf/senate_rules.pdf
* Joint Chamber Rules: http://www.kslegislature.org/li/s/pdf/joint_rules.pdf
* Session Start = January 9, 2023
* Session End = May 22, 2023