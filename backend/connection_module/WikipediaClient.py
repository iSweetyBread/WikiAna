import httpx
import asyncio
import json
import datetime

url = 'https://en.wikipedia.org/w/rest.php/v1/page/Agapanthus/history'

# NOTE: WikipediaClient is to be used when getting data. Use by 'with ... as ...'
class WikipediaClient(httpx.AsyncClient):
    API_URL = 'https://en.wikipedia.org/w/api.php'
    
    def __init__(self, *args, **kwargs):
        headers = {'User-Agent': 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org)'}
        super().__init__(headers=headers, follow_redirects=True, *args, **kwargs)
    
    # General implementation of GET request. Handles retries and timeouts
    async def get(self, url, params, retries = 5, timeout = 5):
        for attempt in range(retries + 1):
            try:
                response = await super().get(url=url, headers=self.headers, params=params)
        
                if response.status_code == 200:
                    return {'success': True, 'response': response}
            except Exception as e:
                print(e)
            
            if attempt < retries:
                await asyncio.sleep(timeout)
        
        return {'success': False, 'response': None}
    
    # Implementation of opensearch functionality
    # Accepts string of text as search query and integer as limit for search suggestions
    # Returns a list of tuples for suggested pages: [(title, description, link), ...]
    async def search(self, query_string, limit = 10):
        params = {
            'action': 'opensearch',
            'namespace': '0',
            'search': query_string,
            'limit': limit,
            'profile': 'fuzzy',
            'format': 'json'
        }
        
        response = await self.get(url=self.API_URL, params=params)
        if response['success']:
            data = json.loads(response['response'].text)
            titles, descs, links = data[1], data[2], data[3]
            result = [(titles[i], descs[i], links[i]) for i in range(len(titles))]            
            return result
        return None
    
    # Gathers article's metadata
    # Accepts a string of text as a title of an article.
    # Returns a dict with basic metadata of all pages found by given title.
    # For details on metadata, see get_info_example.txt
    async def get_info(self, title):
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'info',
            'inprop': 'url|protection|watched|watchlistlabels|watchers|visitingwatchers|notificationtimestamp',
            'format': 'json'
        }
        
        response = await self.get(url=self.API_URL, params=params)
        
        if response['success']:
            data = json.loads(response['response'].text)
            return data['query']['pages'][next(iter(data['query']['pages']))]
        return None
    
    # Gathers article's revision history
    # Accepts a string of text as a title of an article.
    # Optional parameters for date and time (ISO8601) for filtering revisions by time.
    # Returns a list of dicts with data.
    # For details on data, see get_revisions_example.txt
    async def get_revisions(self, title, start_timestamp = '2000-00-01T00:00:00Z', end_timestamp = None):
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'revisions',
            'rvprop': 'ids|flags|timestamp|user|userid|size|comment|content|tags',
            'rvdir': 'newer',
            'rvstart': start_timestamp,
            'rvend': end_timestamp,
            'rvlimit': '50',
            'format': 'json'
        }
        
        result = []
        
        while True:
            response = await self.get(url=self.API_URL, params=params)
            
            if response['success']:
                data = json.loads(response['response'].text)
                revision_data = data['query']['pages'][next(iter(data['query']['pages']))]['revisions']
                result.extend(revision_data)
                
                try:
                    continue_stamp = str(data['continue']['rvcontinue']).split('|')[0]
                    continue_stamp = datetime.datetime.strptime(continue_stamp, "%Y%m%d%H%M%S").isoformat() + 'Z'
                    params['rvstart'] = continue_stamp                    
                except:
                    break
        
        final = list({json.dumps(d, sort_keys=True) for d in result})
        final = [json.loads(d) for d in final]
        
        return final
    
    # Gathers all links towards wikipedia articles inside a particular article
    # Accepts a string of text as a title of an article.
    # Returns a list of tuples for outgoing links: [(title, url), ...]
    async def get_internal_links(self, title):
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'links',
            'plnamespace': '0',
            'pllimit': '500',
            'format': 'json'
        }
        
        raw_result = []
        
        while True:
            response = await self.get(url=self.API_URL, params=params)
            
            if response['success']:
                data = json.loads(response['response'].text)
                link_data = data['query']['pages'][next(iter(data['query']['pages']))]['links']
                raw_result.extend(link_data)
                
                try:
                    plcontinue = data['continue']['plcontinue']
                    params['plcontinue'] = plcontinue
                except:
                    break

        result = []
        for i in raw_result:
            result_title = i['title']
            result_url = (await self.get_info(result_title))['fullurl']
            result.append((result_title, result_url))
        return result
    
    # Gathers user's known languages
    # Accepts a string of text for: user, by any of username, IP, Temporary user, IP range and interwiki name 
    # Returns
    async def get_user_langs(self, user):
        params = {
            'action': 'query',
            'meta': 'babel',
            'babuser': user,
            'format': 'json'
        }
        
        # "babel": {
        #     "de": "1",
        #     "en": "N",
        #     "fr": "1"
        # }
        # TODO: make function to convert dict above to normal language
        response = await self.get(url=self.API_URL, params=params)
        if response['success']:
            data = json.loads(response['response'].text)
            return data['query']['babel']
    
async def main():
    # Usage example
    async with WikipediaClient() as client:
        aaa = await client.get_revisions('Ignatius Sichelbart')
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(aaa, f, ensure_ascii=False, indent=4)
        
asyncio.run(main())