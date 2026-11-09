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
            'rvprop': 'ids|flags|timestamp|user|userid|size|comment|content|tags|sha1',
            'rvdir': 'newer',
            'rvstart': start_timestamp,
            'rvend': end_timestamp,
            'rvlimit': '50',
            'format': 'json',
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
    # Returns a list of tuples for language and level of proficiency: [(English, Native), ...] 
    async def get_user_langs(self, user):
        params = {
            'action': 'query',
            'meta': 'babel',
            'babuser': user,
            'format': 'json'
        }
        
        response = await self.get(url=self.API_URL, params=params)
        if response['success']:
            data = json.loads(response['response'].text)
            processed_data = self.__convert_lang(data['query']['babel'])
            return processed_data
        
    def __convert_lang(self, langs):
        result = []
            
        with open('langs.json', 'r', encoding='utf-8') as f:
            langs_details = json.load(f)
            for i in list(langs.keys()):
                try:
                    result.append((langs_details['language_code'][i], langs_details['proficiency'][langs[i]]))
                except:
                    continue
                    
        return result
    
    # Returns a list of 10 most viewed pages based on last day's pageviews count
    # NOTE: Currently not working; API returns an empty list 
    async def get_top_pages(self):
        params = {
            'action': 'query',
            'list': 'mostviewed',
            'format': 'json'
        }
        
        response = await self.get(url=self.API_URL, params=params)
        if response['success']:
            data = json.loads(response['response'].text)
            return data['query']['mostviewed']
        
    # Finds a random wikipedia article
    # Returns a tuple with article's title and url: (title, url)
    async def get_random_page(self):
        params = {
            'action': 'query',
            'list': 'random',
            'rnnamespace': '0',
            'rnlimit': '1',
            'format': 'json'
        }
        
        response = await self.get(url=self.API_URL, params=params)
        if response['success']:
            data = json.loads(response['response'].text)
            result_title = data['query']['random'][0]['title']
            result_url = (await self.get_info(result_title))['fullurl']
            return (result_title, result_url)
        
    # NOTE: finish later, currently API call returns an empty list
    # NOTE: possible values for ucshow: !autopatrolled, !minor, !new, !patrolled, !top, autopatrolled, minor, new, patrolled, top
    async def get_user_edits(self, username, start_timestamp = '2000-00-01T00:00:00Z', end_timestamp = None, uciprange = None, ucshow = None, uctag = None):
        params = {
            'action': 'query',
            'list': 'usercontribs',
            'uclimit': '500',
            'ucstart': start_timestamp,
            'ucend': end_timestamp,
            'ucuser': username,
            'ucdir': 'newer',
            'ucnamespace': '0',
            'ucprop': 'ids|title|timestamp|comment|parsedcomment|size|sizediff|flags|tags',
            'format': 'json'
        }
        
        return None
    
    # Gathers information about a certain user.
    # Accepts a string of text for username.
    # Returns a dict with various user data.
    # For details on data, see get_user_info_example.txt
    async def get_user_info(self, username):
        params = {
            'action': 'query',
            'list': 'users',
            'ususers': username,
            'usprop': 'blockinfo|groups|groupmemberships|implicitgroups|rights|editcount|registration|emailable|gender|centralids',
            'format': 'json'
        }
            
        response = await self.get(url=self.API_URL, params=params)
        if response['success']:
            data = json.loads(response['response'].text)
            result_data = data['query']['users'][0]
            return result_data
    
    # Gathers a list of blocked users
    # As optional parameters accepts a continue value (bkcontinue), user ids (bkids), usernames (bkusers)
    # Returns a tuple, where [0] element is a list of dictionaries with information on blocked user
    # and [1] element is a continue value (since the list is too large)
    # For details on data, see get_blocked_users_example.txt
    async def get_blocked_users(self, bkcontinue = None, bkids = None, bkusers = None):
        params = {
            'action': 'query',
            'list': 'blocks',
            'format': 'json',
            'bklimit': '500',
            'bkprop': 'id|user|userid|by|byid|timestamp|expiry|reason|parsedreason|range|flags|restrictions',
            'bkcontinue': bkcontinue,
            'bkids': bkids,
            'bkusers': bkusers
        }
                
        result = []
        counter = 0
        
        while counter < 100:
            response = await self.get(url=self.API_URL, params=params)
                    
            if response['success']:
                data = json.loads(response['response'].text)
                block_data = data['query']['blocks']
                result.extend(block_data)
                        
                try:
                    bkcontinue = data['continue']['bkcontinue']
                    params['bkcontinue'] = bkcontinue
                    counter += 1
                except:
                    break
        
        return (result, bkcontinue)
    
    # Gathers a list of all users
    # Accepts optional parameters: start first symbol (aufrom), end first symbol (auto),
    # user prefix (auprefix), filter by user group (augroup), filter by user rights (aurights),
    # filter out inactive users (auactiveusers)
    # Returns a list of dicts with data on users
    # For details on data, see get_users_list_example.txt
    async def get_users_list(self, aufrom = None, auto = None, auprefix = None, augroup = None, aurights = None, auactiveusers = False):
        params = {
            'action': 'query',
            'list': 'allusers',
            'format': 'json',
            'auprefix': auprefix,
            'augroup': augroup,
            'aurights': aurights,
            'auprop': 'blockinfo|groups|implicitgroups|rights|editcount|registration|centralids|tempexpired',
            'aulimit': '500',
            'auactiveusers': auactiveusers,
            'aufrom': aufrom,
            'auto': auto
        }
        
        result = []
        
        while True:
            response = await self.get(url=self.API_URL, params=params)
                                
            if response['success']:
                data = json.loads(response['response'].text)
                user_data = data['query']['allusers']
                result.extend(user_data)
                                    
                try:
                    aufrom = data['continue']['aufrom']
                    params['aufrom'] = aufrom
                except:
                    break
        
        return result
    
    # Gets information on views of a page
    # Accepts a string of text for page title; optional parameter for number of counted days (between 1 and 60)
    # Returns a dict with page view data
    # For details on data, see get_page_views_example.txt 
    async def get_page_views(self, title, pvipdays = 30):
        if pvipdays < 1 and pvipdays > 60:
            raise Exception("Number of days is out of bounds (1-60)")
        
        params = {
            'action': 'query',
            'prop': 'pageviews',
            'titles': title,
            'pvipdays': pvipdays,
            'format': 'json'
        }
        
        response = await self.get(url=self.API_URL, params=params)
        
        if response['success']:
            data = json.loads(response['response'].text)
            page_data = data['query']['pages'][next(iter(data['query']['pages']))]
            return page_data
        return None
    
    # Gathers article's deleted revision history
    # Accepts a string of text as a title of an article.
    # Optional parameters for date and time (ISO8601) for filtering revisions by time.
    # Returns a list of dicts with data.
    # For details on data, see get_deleted_revisions_example.txt
    # TODO: Look up info on deleted revisions and how to view them (typical error: permision denied)
    async def get_deleted_revisions(self, title, start_timestamp = '2000-00-01T00:00:00Z'):
        params = {
            'action': 'query',
            'titles': title,
            'prop': 'deletedrevisions',
            'drvprop': 'ids|flags|timestamp|user|userid|size|comment|content|tags',
            'drvdir': 'newer',
            'drvstart': start_timestamp,
            'drvlimit': '50',
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
    
    # Get a list of contributors to an article
    # Accepts a string of text for an article title
    # Returns a tuple where [0] position is a list of dicts {'userid': ..., 'name': ...}
    # And [1] position is a number of anonymous contributors 
    async def get_page_contributors(self, title):
        params = {
            'action': 'query',
            'prop': 'contributors',
            'titles': title,
            'format': 'json',
            'pclimit': '500'
        }
        
        result = []
        anoncontributors_counter = 0
        
        while True:
            response = await self.get(url=self.API_URL, params=params)
        
            if response['success']:
                data = json.loads(response['response'].text)
                user_data = data['query']['pages'][next(iter(data['query']['pages']))]
                result.extend(user_data['contributors'])
        
                try:
                    pccontinue = data['continue']['pccontinue']
                    params['pccontinue'] = pccontinue
                except:
                    break
        anoncontributors_counter += user_data['anoncontributors']
        
        return (result, anoncontributors_counter)
    
async def main():
    # Usage example
    async with WikipediaClient() as client:
        aaa = await client.get_page_contributors('MediaWiki')
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(aaa, f, ensure_ascii=False, indent=4)
        
asyncio.run(main())