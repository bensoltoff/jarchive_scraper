from BeautifulSoup import BeautifulSoup
import scraperwiki
import datetime
import time
import re

seasons_url = 'http://www.j-archive.com/listseasons.php'
base_url = 'http://www.j-archive.com/'

def scrape_all_seasons(url):

    soup = BeautifulSoup(scraperwiki.scrape(url))
    
    #Grab all of the seasons listed
    seasons = soup.find('div', {"id":"content"}).findAll('a')
    for season in seasons:
        scrape_season(base_url+season['href'])

def scrape_season(url):
    
    soup = BeautifulSoup(scraperwiki.scrape(url))
    
    #Grab the div that contains the content and search for any links
    episodes = soup.find('div', {"id":"content"}).findAll('a',{"href":re.compile('showgame\.php')})
    for episode in episodes:
        
        ep_data = episode.text.split(',')
        ep_num = ep_data[0][5:len(ep_data[0])]

        #Fuck this is messy
        air_data = ep_data[1].split('-')
        air_date = datetime.date (int (air_data[0][12:len(air_data[0])]), int(air_data[1]), int(air_data[2]))
        timestamp = time.mktime(air_date.timetuple())

        scrape_episode(episode['href'], ep_num, timestamp)

def scrape_episode(url, episode, air_date):
    
    soup = BeautifulSoup(scraperwiki.scrape(url))

    allCategories = soup.findAll('td', {"class" : "category_name"})
    cats = [] # List of categories without any html
    for cat in allCategories:
        cats.append(cat.text)

    allClues = soup.findAll(attrs={"class" : "clue"})
    for clue in allClues:

        clue_attribs = get_clue_attribs(clue, cats)
        if clue_attribs:
            clue_attribs['air_date'] = air_date
            clue_attribs['episode'] = episode

            #a shitty unique id but it should do
            clue_attribs['uid'] = str(episode)+clue_attribs['category']+str(clue_attribs['dollar_value'])
            scraperwiki.sql.save(unique_keys=['uid'], data=clue_attribs)



def get_clue_attribs(clue, cats):
    #Because of the way jarchive hides the answers to clues
    #this is here to keep things a bit more tidy
    div = clue.find('div')
    
    if div:
        #Split the JS statement into it's arguments so we can extract the html from the final argument
        mouseover_js = div['onmouseover'].split(",",2)
        answer_soup = BeautifulSoup(mouseover_js[2]) #We need to go... deeper
        answer = answer_soup.find('em', {"class" : "correct_response"}).text
        
        #Was this a triple stumper?
        triple_stumper = answer_soup.find(text="Triple Stumper") == "Triple Stumper"
                           
        #Now to figure out the category
        clue_id = clue.find(attrs={"class" : "clue_unstuck"})['id'].split("_")[1:4] #contains the unique ID of the clue for this specific game
                                                                                    #format: clue_["DJ"||"J"]_[Category(1-6)]_[Row(1-5)]_unstuck
        #Adjust for if the clue is in Jeopardy or Double Jeopardy
        if clue_id[0] == 'J':
            cat = cats[int(clue_id[1])-1]
        elif clue_id[0] == 'DJ':
            cat = cats[int(clue_id[1])+6-1]
        
        #Are we in double jeopardy?
        dj = clue_id[0] == "DJ"

        #What is the question difficulty (i.e. what row is the clue in?)
        clue_row = clue_id[2]

        #The class name for the dollar value varies if it's a daily double
        dollar_value = clue.find(attrs={"class" : re.compile('clue_value*')}).text
        clue_text = clue.find(attrs={"class" : "clue_text"}).text
        clue_order_number = clue.find(attrs={"class" : "clue_order_number"}).text
        
        return {"answer" : answer, "category" : cat, "text" : clue_text, "dollar_value": dollar_value, "order_number" : clue_order_number, "dj" : dj, "triple_stumper" : triple_stumper, "clue_row" : clue_row}

#scrape_all_seasons(seasons_url)
scrape_season(base_url+"showseason.php?season=30")


###Test on sample of episodes in test directory
##import os
##root = r'F:\Google Drive\Documents\Github\jarchive_scraper\test'
##
##for file in os.listdir(root):
##    filename = "file:\\\\\\" + os.path.join(root,file)
##    print filename
##    scrape_episode(filename, file, file)





