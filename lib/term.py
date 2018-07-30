from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus
import urllib.request
import html5lib
#pip install html5lib
query = 'python get top 10 google results with beautiful soup'
base_url = 'https://www.google.com/search?'
results = 100
hdr = {'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}
headers={'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'} 


url = base_url + urlencode({'q' : query, 'num' : results}, quote_via=quote_plus)
req = urllib.request.Request(url, headers=hdr)
response = urllib.request.urlopen(req)

soup = BeautifulSoup(response.read(), "html5lib")
links = soup.findAll("a")
for link in links:
    link_href = link.get('href')
    if "url?q=" in link_href and not "webcache" in link_href:
        print(link.get('href').split("?q=")[1].split("&sa=U")[0])