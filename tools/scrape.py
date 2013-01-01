# packages: html5lib, beautifulsoup4

from bs4 import BeautifulSoup
import sys, re, csv, requests
from optparse import OptionParser

parser = OptionParser()

parser.add_option("-g", dest="gush", help="get data for Gush# (required)")
parser.add_option("-o", dest="filename", default=sys.stdout, help="save output to filename (if empty will use STDOUT)")
parser.add_option("-q", dest="quiet", default=False, action="store_true", help="and be quiet about it")

(options, args) = parser.parse_args()
quiet = options.quiet

# because optparse, instead of just providing a required=True param, provides a Python-anal discourse on the meaning of "Option"
gush = options.gush
if gush is None:
	print "Must include a Gush# (run with --help to see all options)"
	exit()

download_url = "http://mmi.gov.il/IturTabot/taba2.asp?Gush=%s&fromTaba1=true" % gush

if not quiet: 
	print "Downloading gush# %s from %s" % (gush, download_url)

try:
	r = requests.get(download_url)
	if r.status_code != 200:
		raise Exception("Status code: %s" % r.status_code)
except Exception, e:
	print "ERROR: %s" % e
	exit()

r.encoding = 'windows-1255'
content = r.text


if options.filename is None:
	output_file = sys.stdout
else:
	output_file = open(options.filename, "wb")

c = csv.writer(output_file)
c.writerow(["gush", "area", "number", "details_link", "status", "date", "essence", "takanon_link", "tasrit_link", "nispahim_link", "files_link", "govmap_link"])


# content = open("results_page.html").read()
s = BeautifulSoup(content, from_encoding = r.encoding)


# parse the HTML
# note: the parsing intentionally uses attrs like width which are likely to change.
# the goal is to be fragile, so that if the HTML changes the parsing breaks rather than parse incorrectly.
# TODO add tests for the same table structure and alerts if broken

# get the data table. this is the 30th table on the page
table = s("table", "highLines")[0]

# helper functions to clean up some hrefs
def extract_popoutpdf(js):
	return "http://mmi.gov.il/%s" % js.replace("javascript:PopOutPdf('", "").replace("');", "")

def extract_popoutmmg(js):
	return js.replace("javascript:PopOutMmg('", "").replace("');", "")

for tr in table("tr", valign="top"):

	area = ''; number = ''; details_link = ''; status = ''; date = ''; essence = ''
	takanon_link = []; tasrit_link = []; nispahim_link = []; files_link = []; govmap_link = []

	area 	= tr("td", width="80")[0].get_text(strip=True).encode('utf-8')
	number 	= tr("td", width="120")[0].get_text(strip=True).encode('utf-8')
	details_link 	= tr("td", width="120")[0].a.get("href")
	
	status 	= tr("td", width="210")[0].get_text(strip=True).encode('utf-8')
	
	matchdate=re.search(r'(\d+/\d+/\d+)', status)
	if matchdate:
		date = matchdate.group(1)
		status = status.replace(date, '')
	
	essence = tr("td", width="235")[0].get_text(strip=True).encode('utf-8')

	if tr("td", width="40")[0].a:
		for i in tr("td", width="40")[0].find_all("a"):
			takanon_link.append(extract_popoutpdf(i.get("href")))

	if tr("td", width="40")[1].a:
		for i in tr("td", width="40")[1].find_all("a"):
			tasrit_link.append(extract_popoutpdf(i.get("href")))

	if tr("td", width="55")[0].a:
		for i in tr("td", width="55")[0].find_all("a"):
			nispahim_link.append(extract_popoutpdf(i.get("href")))

	if tr("td", width="40")[2].a:
		for i in tr("td", width="40")[2].find_all("a"):
			url = i.get("href")
			if url.endswith(".zip"):
				files_link.append(url)
			elif "PopUpMmg" in url:
				govmap_link.append(extract_popupmmg(url))

	if not quiet:
		print gush, area, number, details_link, status, date, essence, takanon_link, tasrit_link, nispahim_link, files_link, govmap_link
	
	c.writerow([gush, area, number, details_link, status, date, essence, takanon_link, tasrit_link, nispahim_link, files_link, govmap_link])
