from datetime import datetime, timedelta
from utils import logger
import httpx

query_data = '''
query ($id: Int) {
    Media(id: $id, type: ANIME) {
        id
        title {
            romaji
            english
        }
        coverImage {
            large
        }
        nextAiringEpisode {
            airingAt
            episode
        }
        episodes
        status
        startDate {
            year
            month
            day
        }
        endDate {
            year
            month
            day
        }
        duration
        season
        format
        studios {
            edges {
                node {
                    name
                }
            }
        }
    }
}
'''

search_query = '''
query ($search: String) {
  Page(page: 1, perPage: 20) {
    media(search: $search, type: ANIME) {
    id
    title {
        romaji
        english
    }
    nextAiringEpisode {
        airingAt
        episode
    }
    coverImage {
        large
    }
    episodes
    status
    startDate {
        year
        month
        day
    }
    endDate {
        year
        month
        day
    }
    duration
    season
    format
    studios {
        edges {
          node {
            name
          }
        }
      }
    }
  }
}
'''

query_airing = '''
query AiringAnimes($page: Int, $perPage: Int, $sort: [AiringSort], $airingAtGreater: Int, $airingAtLesser: Int) {
    Page(page: $page, perPage: $perPage) {
        airingSchedules(sort: $sort, airingAt_greater: $airingAtGreater, airingAt_lesser: $airingAtLesser) {
            id
            mediaId
            media {
                id
                title {
                    romaji
                }
                coverImage {
                    large
                }
            }
            episode
            airingAt
        }
    }
}
'''

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

cache = {}

async def post(url, json):
    async with httpx.AsyncClient() as client:
        resp = await client.post(url=url, json=json, headers=headers, timeout=100000)
        return resp

async def get_time():
    now = datetime.now()
    start_of_day = datetime(now.year, now.month, now.day)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
    return int(start_of_day.timestamp()), int(end_of_day.timestamp())

async def fetch_today(page):
    start_of_today, end_of_today = await get_time()
    variables = {
        "page": page,
        "perPage": 50,
        "sort": ["TIME"],
        "airingAtGreater": start_of_today,
        "airingAtLesser": end_of_today
    }
    try:
        response = await post(url='https://graphql.anilist.co', json={'query': query_airing, "variables": variables})
        if response.status_code == 200:
            json_stuff = response.json()
            return json_stuff["data"]["Page"]["airingSchedules"]
        return 404
    except httpx.HTTPError as err:
        logger.error(err)
        return 404
    except Exception as err:
        logger.error(err)
        return 404

async def get_today_anime():
    tmp_data = []
    for num in range(1, 2147483647):
        data = await fetch_today(num)
        tmp_data.extend(data)
        if len(data) < 50:
            return tmp_data
        
async def fetch_details(anime: int) -> dict:
    """Taking details from anime using id"""
    try:
        response = await post(url='https://graphql.anilist.co', json={'query': query_data, 'variables': {'id': int(anime)}})
        if response.status_code == 200:
            return response.json()["data"]["Media"]
        logger.error(f"Error {response.status_code} in id: {anime}")
        return response.status_code
    except Exception as e:
        logger.error(e)
        return 404

async def fetch_search(title: str) -> dict:
    """Searching anime by title"""
    try:
        response = await post(url='https://graphql.anilist.co', json={'query': search_query, 'variables': {'search': title}})
        if response.status_code == 200:
            return response.json()["data"]["Page"]["media"]
        logger.error(f"Error {response.status_code} in name: {title}")
        return response.status_code
    except Exception as e:
        logger.error(e)
        return 404

async def search_anime(data: str):
    if data in cache:
        return cache[data]
    else:
        if data.isdigit():
            details = await fetch_details(int(data))
        else:
            details = await fetch_search(data)
        
        if details != 404 and details != [] and isinstance(details, list):
            cache[data] = details[0]
            return details[0]
        cache[data] = details
        return details