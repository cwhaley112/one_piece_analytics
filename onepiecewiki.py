import requests
from bs4 import BeautifulSoup as bs
import json

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

def clean(elem):
	# might need to use regex if this gets too complicated
	if type(elem)==str:
		return elem.replace('\u00a0', ' ')
	elif type(elem)==list:
		for i in range(len(elem)):
			elem[i] = clean(elem[i])
		return elem
	elif type(elem)==dict:
		for key in elem.keys():
			elem[key] = clean(elem[key])

try:
	for chapter in range(1,10):#1070):
		print(chapter)
		d=dict()
		url = url_base+str(chapter)
		r = requests.get(url)
		html = bs(r.text, 'html.parser')

		text = html.find(id='mw-content-text').get_text()
		split = [seq.strip() for seq in text.split('\n\n') if len(seq.strip())>0]
		# print(split)


		# let's scrape the main text and store a bunch of data

		# volume#, viz title, page count, release date
		d['Title']=clean(split[0])
		d['Viz Title'] = clean(grab('Viz Title', split))
		d['Pages']= clean(grab('Pages', split))
		d['Volume']= clean(grab('Volume', split))
		temp = grab('Release Date:', split)
		if temp[-5:]=='[ref]': temp = temp[:-5]
		d['Release Date'] = clean(temp)

		# cover page text
		if chapter not in [4,6,1024]: # these chapters do not have cover pages
			d['Cover Page'] = clean(grab('Cover Page', split, skip=1))
		else:
			d['Cover Page'] = ''

		# short summary, long summary
		d['Short Summary'] = clean(grab('Short Summary', split, skip=1))
		d['Long Summary'] = clean(grab('Long Summary', split, skip=1, occ='all'))

		# chapter notes
		d['Chapter Notes'] = clean(grab('Quick Reference', split, occ='list', skip=1)[1:-1]) # 2nd to last elem in quick references, last is 'Characters' header

		# characters (+ their affiliations and any parenthetical sidenotes)
		# this one is soooo annoying

		table = [elem for elem in html.find_all('table') if elem['class'][0]=='CharTable'][0]
		# print(table)
		charmap = {}

		# character groups (pirates, marines, civilians, etc.)
		groups = [elem.text.strip() for elem in table.find_all('tr')[0].find_all('th')]
		
		# get number of subgroups per group
		colspans = [int(elem['colspan']) if elem.has_attr('colspan') else 1 for elem in table.find_all('tr')[0].find_all('th')]

		# Necessary because some subgroup titles don't have <a> tags and it messes with my code :(
		subgrouptitles = [cell.find('dl').find('dt').text for cell in table.find_all('tr')[1].find_all('td') if cell.find('dl') is not None]
		# subgroups: first elem is subgroup title, subsequent elements are character names
		subgroups = [[elem.text for elem in cell.find_all('a')] for cell in table.find_all('tr')[1].find_all('td')]
		print(groups)
		print(subgroups)
		print(colspans)
		print(subgrouptitles)

		sg_ix = 0
		sgtitle_ix = 0
		for i, group in enumerate(groups):
			num = colspans[i]
			if num>1:
				newgroup = dict()
				while num>0:
					num-=1
					subgroup = subgroups[sg_ix]
					if subgroup[0]==subgrouptitles[sgtitle_ix]:
						newgroup[subgroup[0]] = subgroup[1:]
					else:
						newgroup[subgrouptitles[sgtitle_ix]] = subgroup
					sg_ix+=1
					sgtitle_ix+=1
			else:
				newgroup = subgroups[sg_ix]
				sg_ix+=1
			charmap[group] = newgroup

		# print(charmap)

		d['Characters']= charmap

		data[chapter]=d
		# break
except KeyboardInterrupt as e:
	pass


# with open('chapters.json', 'w') as f:
# 	json.dump(data, f, indent=4)