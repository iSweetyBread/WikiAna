import httpx
import asyncio
import json

url = 'https://en.wikipedia.org/w/rest.php/v1/page/Agapanthus/history'

# NOTE: WikipediaClient is to be used when getting data. Use by 'with ... as ...'
class WikipediaClient(httpx.AsyncClient):
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
                asyncio.sleep(timeout)
        
        return {'success': False, 'response': None}
    
    # Implementation of opensearch functionality
    # Accepts string of text as search query and integer as limit for search suggestions
    # Returns a list of tuples for suggested pages: [(title, description, link), ...]
    async def search(self, query_string, limit = 10):
        url = 'https://en.wikipedia.org/w/api.php'
        params = {
            'action': 'opensearch',
            'namespace': '0',
            'search': query_string,
            'limit': limit,
            'profile': 'fuzzy',
            'format': 'json'
        }
        
        response = await self.get(url=url, params=params)
        if response['success']:
            data = json.loads(response['response'].text)
            titles, descs, links = data[1], data[2], data[3]
            result = [(titles[i], descs[i], links[i]) for i in range(len(titles))]            
            return result
        return None
    
    # Accepts a string of text as a title for an article.
    # Returns a dict with basic metadata of all pages found by given title.
    # For details on metadata, see get_info_example.txt
    async def get_info(self, title):
        url = 'https://en.wikipedia.org/w/api.php'
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'info',
            'inprop': 'url|protection|watched|watchlistlabels|watchers|visitingwatchers|notificationtimestamp',
            'format': 'json'
        }
        
        response = await self.get(url=url, params=params)
        if response['success']:
            data = json.loads(response['response'].text)
            return data['query']['pages']
        return None
    
async def main():
    # Usage example
    async with WikipediaClient() as client:
        aaa = await client.get_info('Hampi')
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(aaa, f, ensure_ascii=False, indent=4)
        
asyncio.run(main())