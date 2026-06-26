"""
Moduł scrapera – pobiera recenzje i dyskusje forumowe ze Steam.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def fetch_steam_reviews(appid: str, count: int = 100) -> list[dict]:
    """
    Pobiera najnowsze recenzje gry ze Steam Web API.
    Zwraca listę słowników z kluczami: id, type, author, title, content, url, voted_up.
    """
    url = (
        f"https://store.steampowered.com/appreviews/{appid}"
        f"?json=1&filter=recent&language=all&num_per_page={count}&cursor=*"
    )
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        raise ConnectionError(f"Nie udało się pobrać recenzji: {e}")

    reviews = []
    if data.get('success') and 'reviews' in data:
        for rev in data['reviews']:
            rec_id = str(rev['recommendationid'])
            author_id = rev['author']['steamid']
            voted_up = rev.get('voted_up', True)
            content = rev.get('review', '')
            playtime = rev['author'].get('playtime_forever', 0)

            reviews.append({
                'id': f"rev_{rec_id}",
                'type': 'Recenzja',
                'author': f"Gracz ({author_id})",
                'title': 'Pozytywna recenzja' if voted_up else 'Negatywna recenzja',
                'content_orig': content,
                'content_trans': '',
                'sentiment': 'positive' if voted_up else 'negative',
                'url': f"https://steamcommunity.com/profiles/{author_id}/recommended/{appid}/",
                'voted_up': voted_up,
                'playtime_hours': round(playtime / 60, 1),
                'created_at': datetime.utcfromtimestamp(rev.get('timestamp_created', 0)).isoformat(),
                'timestamp_updated': datetime.utcfromtimestamp(rev.get('timestamp_updated', 0)).isoformat() if rev.get('timestamp_updated') else None,
                'developer_response': rev.get('developer_response', None)
            })
    return reviews





def fetch_game_info(appid: str) -> dict | None:
    """Pobiera podstawowe informacje o grze ze Steam Store API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        if data.get(str(appid), {}).get('success'):
            game_data = data[str(appid)]['data']
            price_overview = game_data.get('price_overview', {})
            price = price_overview.get('final_formatted', 'Brak danych')
            if game_data.get('is_free'):
                price = "Darmowa"
            
            return {
                'name': game_data.get('name', 'Nieznana gra'),
                'header_image': game_data.get('header_image', ''),
                'short_description': game_data.get('short_description', ''),
                'developers': game_data.get('developers', []),
                'genres': [g['description'] for g in game_data.get('genres', [])],
                'price': price,
            }
    except Exception:
        pass
    return None

def fetch_game_stats(appid: str) -> dict:
    """Pobiera globalne statystyki recenzji gry ze Steam."""
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language=all&num_per_page=0"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        if 'query_summary' in data:
            qs = data['query_summary']
            return {
                'total_reviews': qs.get('total_reviews', 0),
                'total_positive': qs.get('total_positive', 0),
                'total_negative': qs.get('total_negative', 0),
                'review_score_desc': qs.get('review_score_desc', 'Brak danych')
            }
    except Exception:
        pass
    return {'total_reviews': 0, 'total_positive': 0, 'total_negative': 0, 'review_score_desc': 'Błąd pobierania'}


def fetch_player_stats(appid: str) -> dict:
    """Pobiera aktualną liczbę graczy (Steam) i peak CCU (SteamSpy)."""
    result = {'current': 0, 'peak_ccu': 0}
    try:
        r = requests.get(
            f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}",
            headers=HEADERS, timeout=8
        )
        result['current'] = r.json().get('response', {}).get('player_count', 0)
    except Exception:
        pass
    try:
        # SteamCharts frequently updates and shows All-Time Peak clearly
        sc_resp = requests.get(f"https://steamcharts.com/app/{appid}", headers=HEADERS, timeout=8)
        if sc_resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(sc_resp.text, 'html.parser')
            # The structure is usually <div class="app-stat"> ... <span class="num">PEAK</span> ... </div>
            stat_divs = soup.select('.app-stat')
            for div in stat_divs:
                if 'All-Time Peak' in div.text:
                    num_str = div.select_one('.num').text.strip().replace(',', '')
                    result['peak_ccu'] = int(num_str)
                    break
    except Exception:
        pass

    if not result['peak_ccu']:
        # Fallback to SteamSpy (shows max CCU for recent days usually)
        try:
            r = requests.get(
                f"https://steamspy.com/api.php?request=appdetails&appid={appid}",
                timeout=12
            )
            result['peak_ccu'] = r.json().get('peak_ccu', 0)
        except Exception:
            pass
    return result


def fetch_steam_news(appid: str, count: int = 20) -> list[dict]:
    """Pobiera najnowsze newsy / devlogi dla gry ze Steam."""
    url = (
        f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
        f"?appid={appid}&count={count}&maxlength=1000&format=json"
    )
    DEVLOG_KW = ['dev', 'update', 'patch', 'hotfix', 'fix', 'log', 'devlog',
                 'weekly', 'notes', 'development', 'release']
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        items = r.json().get('appnews', {}).get('newsitems', [])
        news = []
        for item in items:
            title_l = item.get('title', '').lower()
            news.append({
                'gid':       item.get('gid', ''),
                'title':     item.get('title', ''),
                'date':      item.get('date', 0),   # Unix timestamp
                'contents':  item.get('contents', ''),
                'url':       item.get('url', ''),
                'feedname':  item.get('feedname', ''),
                'is_devlog': any(kw in title_l for kw in DEVLOG_KW),
                'comment_count': item.get('comment_count', 0),
                'upvotes':   item.get('upvotes', 0)
            })
        return news
    except Exception:
        return []
