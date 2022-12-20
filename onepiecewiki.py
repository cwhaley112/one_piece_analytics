import requests
from bs4 import BeautifulSoup as bs

data=dict()
url_base = "https://onepiece.fandom.com/wiki/Chapter_"

def find(lst, elem, nocaps=False, skip=0):
	for i in range(len(lst)):
		if (nocaps and elem.lower() in lst[i].lower()) or (elem in lst[i]):
			if skip: 
				skip-=1
				continue
			return i
	return -1

def extract(seq, occ):
	if occ=='all':
		return ' '.join(seq.split('\n')[1:])
	elif occ=='list':
		return seq.split('\n')[1:]
	return seq.split('\n')[occ]

def grab(text, seq, nocaps=False, occ=-1, skip=0):
	return extract(seq[find(seq, text, nocaps=nocaps, skip=skip)], occ=occ)

for chapter in range(1,1070):
	d=dict()
	url = url_base+str(chapter)
	r = requests.get(url)
	html = bs(r.text, 'html.parser')

	text = html.find(id='mw-content-text').get_text()
	split = [seq.strip() for seq in text.split('\n\n') if len(seq.strip())>0]
	# print(split)


	# let's scrape the main text and store a bunch of data

	# volume#, viz title, page count, release date
	d['Title']=split[0]
	d['Viz Title'] = grab('Viz Title', split)
	d['Pages']=grab('Pages', split)
	d['Volume']=grab('Volume', split)
	temp = grab('Release Date:', split)
	if temp[-5:]=='[ref]': temp = temp[:-5]
	d['Release Date'] = temp

	# cover page text
	d['Cover Page'] = grab('Cover Page', split, skip=1)

	# short summary, long summary
	d['Short Summary'] = grab('Short Summary', split, skip=1)
	d['Long Summary'] = grab('Long Summary', split, skip=1, occ='all')

	# chapter notes
	d['Chapter Notes'] = grab('Quick Reference', split, occ='list', skip=1)[1:-1] # 2nd to last elem in quick references, last is 'Characters' header

	# characters (+ their affiliations and any parenthetical sidenotes)
	# this one may have several edge cases
	# might need to do more html parsing for this



	data[chapter]=d
	break
print(data)