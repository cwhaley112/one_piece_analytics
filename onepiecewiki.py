import requests
from bs4 import BeautifulSoup as bs
import json
import pandas as pd

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
	# for chapter in range(800,801):#1070):
	# for chapter in range(7,0,-1):
	for chapter in range(4,5):
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

		# Each group can have subgroups (e.g., straw hats within pirates, captains within marines)
		# sub_titles = [cell for cell in table.find_all('tr')[1].find_all('td') if cell.find('dl')]
		sub_titles = [cell if cell.find('dl') else '' for cell in table.find_all('tr')[1].find_all('td')]
		# subgroups: first elem is subgroup title, subsequent elements are character names
		# exeption being when there are multiple subgroups in one column (handled later)
		subgroups = [[elem.text for elem in cell.find_all('a')] for cell in table.find_all('tr')[1].find_all('td')]
		temp1 = [subelem.find('dt') if subelem.find('dt') is not None else subelem.find('li') for cell in table.find_all('tr')[1].find_all('td') for subelem in cell.find_all(['dl','ul'])]
		temp2 = [subelem for cell in table.find_all('tr')[1].find_all('td') for subelem in cell.find_all(['dl','ul'])]
		for i in range(len(temp1)):
			print(temp1[i], temp2[i], None if temp1[i] is None else temp1[i].text, '\n', sep='\n\n')
		assert False
		subgrouptitles = [subelem.find('dt').text for cell in table.find_all('tr')[1].find_all('td') if cell.find('dl') is not None for subelem in cell.find_all('dl')]

		
		# some groups have multiple columns, and some columns have multiple subgroups
		colspans = [int(elem['colspan']) if elem.has_attr('colspan') else 1 for elem in table.find_all('tr')[0].find_all('th')]
		rowspans = [len(cell.find_all('hr'))+1 if type(cell)!=str else 1 for cell in sub_titles] # <hr> is a row break
		
		print(groups)
		print(subgroups)
		print(colspans)
		print(rowspans)
		print(subgrouptitles)
		print('\n\n')
		# print(sub_titles)

		# parse table into json format
		sg_ix = 0
		sgtitle_ix = 0
		# for each main group (has column header)
		for i, group in enumerate(groups):
			# get number of subcolumns
			num = colspans[i]
			if num>1:
				# if more than one column, loop through each subcolumn
				newgroup = dict()
				while num>0:
					num-=1
					rowspan = rowspans[sg_ix]
					subgroup = subgroups[sg_ix]

					# if there are multiple subgroups in the column, then loop through the names.
					# otherwise, put the whole subgroup into newgroup
					if rowspan==1:
						if sgtitle_ix < len(subgrouptitles) and subgroup[0] == subgrouptitles[sgtitle_ix]:
							newgroup[subgrouptitles[sgtitle_ix]] = subgroup[1:]
						else:
							newgroup[subgrouptitles[sgtitle_ix]] = subgroup
						sgtitle_ix+=1
					else:
						start=0
						for j in range(rowspan):
							# for each subrow in the subcolumn, extract all information
							sgtitle = subgrouptitles[sgtitle_ix]

							# figure out which elements are in the subgroup
							if j==rowspan-1:
								end = len(subgroup) # go to end of list
							else:
								end = subgroup.index(subgrouptitles[sgtitle_ix+1]) # get index where next subgroup starts
							newgroup[subgrouptitles[sgtitle_ix]] = subgroup[start+1:end]
							start = end
							sgtitle_ix+=1
					sg_ix+=1
					
			else:
				# new logic:
				newgroup = dict()
				rowspan = rowspans[sg_ix]
				subgroup = subgroups[sg_ix]
				print(rowspan, subgroup, sg_ix, sgtitle_ix)

				# if there are multiple subgroups in the column, then loop through the names.
				# otherwise, put the whole subgroup into newgroup
				if rowspan==1:
					if sgtitle_ix < len(subgrouptitles) and subgroup[0] == subgrouptitles[sgtitle_ix]:
						newgroup[subgrouptitles[sgtitle_ix]] = subgroup[1:]
					else:
						newgroup[subgrouptitles[sgtitle_ix]] = subgroup
					sgtitle_ix+=1
				else:
					start=0
					for j in range(rowspan):
						# for each subrow in the subcolumn, extract all information
						sgtitle = subgrouptitles[sgtitle_ix]

						# figure out which elements are in the subgroup
						if j==rowspan-1:
							end = len(subgroup) # go to end of list
						elif subgrouptitles[sgtitle_ix+1] in subgroup:
							end = subgroup.index(subgrouptitles[sgtitle_ix+1]) # get index where next subgroup starts
						else:
							# subgroup that didn't have an <a> html tag so I have no idea where it ends
							# temp solution: categorize everything else as "other"
							# TODO
							newgroup['Others'] = subgroup[start+1:]
							sgtitle_ix+=2
							break
						newgroup[subgrouptitles[sgtitle_ix]] = subgroup[start+1:end]
						start = end
						sgtitle_ix+=1
				sg_ix+=1
				
				# old logic:
				# subgroup = subgroups[sg_ix]
				# if sgtitle_ix < len(subgrouptitles) and subgroup[0] == subgrouptitles[sgtitle_ix]:
				# 	newgroup = {subgroup[0]: subgroup[1:]}
				# 	# sgtitle_ix+=1
				# else:
				# 	newgroup = subgroup
				# sg_ix+=1
			charmap[group] = newgroup

		print(charmap)

		d['Characters']= charmap

		data[chapter]=d
		# break
except KeyboardInterrupt as e:
	pass


with open('test.json', 'w') as f:
	json.dump(data, f, indent=4)