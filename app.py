"""
🎮 Steam Support Dashboard
Główny plik aplikacji Streamlit.
"""
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from db import init_db, get_items, get_stats, archive_item, restore_item, delete_item, insert_item
from scraper import fetch_steam_reviews, fetch_game_info, fetch_game_stats, fetch_player_stats, fetch_steam_news
from translator import translate_to_pl

# ── Konfiguracja strony ──────────────────────────────────────────
st.set_page_config(
    page_title="Steam Support Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()

# ── CSS ──────────────────────────────────────────────────────────
st.html("""
<style>


    /* Gradient sidebar headers */
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        background: linear-gradient(135deg, #A78BFA, #7C3AED) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(139,92,246,0.04)) !important;
        border: 1px solid rgba(124,58,237,0.2) !important;
        border-radius: 16px !important;
        padding: 20px 24px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(124,58,237,0.5) !important;
        box-shadow: 0 8px 32px rgba(124,58,237,0.15) !important;
        transform: translateY(-2px) !important;
    }
    div[data-testid="stMetric"] label {
        color: #94A3B8 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #E2E8F0, #A78BFA) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 12px 28px !important;
        border-radius: 12px 12px 0 0 !important;
    }
    button[data-baseweb="tab"]:hover {
        background: rgba(124,58,237,0.1) !important;
    }

    /* ── Karty: pozytywne ── */
    [class*="st-key-card_pos_"] {
        background: linear-gradient(135deg, rgba(34,197,94,0.07), rgba(34,197,94,0.02)) !important;
        border: 1px solid rgba(34,197,94,0.25) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease !important;
    }
    [class*="st-key-card_pos_"]:hover {
        border-color: rgba(34,197,94,0.5) !important;
        box-shadow: 0 4px 20px rgba(34,197,94,0.1) !important;
    }

    /* ── Karty: negatywne ── */
    [class*="st-key-card_neg_"] {
        background: linear-gradient(135deg, rgba(239,68,68,0.07), rgba(239,68,68,0.02)) !important;
        border: 1px solid rgba(239,68,68,0.25) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease !important;
    }
    [class*="st-key-card_neg_"]:hover {
        border-color: rgba(239,68,68,0.5) !important;
        box-shadow: 0 4px 20px rgba(239,68,68,0.1) !important;
    }

    /* ── Karty: forum ── */
    [class*="st-key-card_forum_"] {
        background: linear-gradient(135deg, rgba(59,130,246,0.07), rgba(59,130,246,0.02)) !important;
        border: 1px solid rgba(59,130,246,0.25) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        transition: all 0.3s ease !important;
    }
    [class*="st-key-card_forum_"]:hover {
        border-color: rgba(59,130,246,0.5) !important;
        box-shadow: 0 4px 20px rgba(59,130,246,0.1) !important;
    }

    /* ── Karty: archiwum ── */
    [class*="st-key-card_arch_"] {
        background: linear-gradient(135deg, rgba(100,116,139,0.07), rgba(100,116,139,0.02)) !important;
        border: 1px solid rgba(100,116,139,0.2) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        opacity: 0.85 !important;
        transition: all 0.3s ease !important;
    }
    [class*="st-key-card_arch_"]:hover {
        opacity: 1 !important;
        border-color: rgba(100,116,139,0.4) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(124,58,237,0.25) !important;
    }
    .stLinkButton > a {
        border-radius: 12px !important;
        font-weight: 600 !important;
    }

    /* Divider */
    .gradient-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(124,58,237,0.4), transparent);
        border: none;
        margin: 20px 0;
    }

    /* Genre tags */
    .genre-tag {
        display: inline-block;
        background: rgba(124,58,237,0.15);
        color: #A78BFA;
        padding: 2px 10px;
        border-radius: 8px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 6px;
        margin-top: 6px;
    }
</style>
""")


# ── NAGŁÓWEK I OPCJE ─────────────────────────────────────────────
st.markdown("# 🎮 Dev & Player Support Dashboard")
st.caption("Monitoruj recenzje i dyskusje graczy ze Steam — tłumacz, filtruj i zarządzaj w jednym miejscu.")

col1, col2 = st.columns([1, 2])
with col1:
    appid = st.text_input("🔑 Steam AppID", value="3710840", help="Wpisz identyfikator gry ze Steam.")
    if st.button("🔄 Pobierz nowe dane", use_container_width=True, type="primary"):
        with st.spinner("⏳ Pobieranie i tłumaczenie..."):
            added = 0
            errors = []

            try:
                for rev in fetch_steam_reviews(appid):
                    item = {
                        'id': rev['id'],
                        'appid': appid,
                        'type': rev['type'],
                        'author': rev['author'],
                        'title': translate_to_pl(rev['title']),
                        'content_orig': rev['content_orig'],
                        'content_trans': translate_to_pl(rev['content_orig']),
                        'url': rev['url'],
                        'sentiment': rev['sentiment'],
                        'created_at': rev.get('created_at'),
                        'timestamp_updated': rev.get('timestamp_updated'),
                        'developer_response': rev.get('developer_response')
                    }
                    if insert_item(item):
                        added += 1
            except ConnectionError as e:
                errors.append(str(e))

            for err in errors:
                st.error(err)
            if added > 0:
                st.success(f"✅ Dodano **{added}** nowych wpisów!")
                st.rerun()
            elif not errors:
                st.info("Brak nowych wpisów do dodania.")

with col2:
    if appid:
        game_info = fetch_game_info(appid)
        if game_info:
            c_img, c_txt = st.columns([1, 6])
            with c_img:
                if game_info.get('header_image'):
                    st.image(game_info['header_image'], use_container_width=True)
            with c_txt:
                st.markdown(f"### {game_info['name']}")
                devs = ", ".join(game_info['developers']) if game_info['developers'] else "Brak danych"
                genres = " • ".join(game_info['genres'][:5]) if game_info['genres'] else "Brak gatunku"
                st.caption(f"🏢 **Firma:** {devs} | 🏷️ **Gatunek:** {genres}")

st.html('<div class="gradient-divider"></div>')

# ── STATYSTYKI I WYKRES (NA START) ───────────────────────────────

def _parse_rev_date(review: dict, fallback):
    """Bezpiecznie parsuje created_at recenzji do date."""
    try:
        return datetime.fromisoformat(str(review.get('created_at', ''))).date()
    except Exception:
        return fallback


if 'active_sentiment' not in st.session_state:
    st.session_state.active_sentiment = 'all'

global_stats = fetch_game_stats(appid) if appid else {'total_reviews': 0, 'total_positive': 0, 'total_negative': 0}
total_revs = global_stats.get('total_reviews', 0)
total_pos = global_stats.get('total_positive', 0)
total_neg = global_stats.get('total_negative', 0)

if total_revs > 0:
    percent_pos = (total_pos / total_revs) * 100
    if percent_pos >= 80:
        sentiment_emoji = "😍 Znakomite"
    elif percent_pos >= 70:
        sentiment_emoji = "😊 Pozytywne"
    elif percent_pos >= 40:
        sentiment_emoji = "😐 Mieszane"
    else:
        sentiment_emoji = "😡 Negatywne"
        
    local_reviews = [i for i in get_items(0, appid) if i['type'] == 'Recenzja']
    
    st.markdown("### 📊 Analiza Sentymentu")

    # Pobierz statystyki graczy
    player_stats = fetch_player_stats(appid) if appid else {'current': 0, 'peak_ccu': 0}

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Pozytywne recenzje (%)", f"{percent_pos:.1f}%")

    # Nastawienie — HTML badge (metric nie obsługuje emoji)
    emoji_parts  = sentiment_emoji.split(' ', 1)
    emoji_icon   = emoji_parts[0] if len(emoji_parts) > 1 else ''
    emoji_label  = emoji_parts[1] if len(emoji_parts) > 1 else sentiment_emoji
    col_s2.html(f"""
        <div style="background:linear-gradient(135deg,rgba(124,58,237,0.08),rgba(139,92,246,0.04));
                    border:1px solid rgba(124,58,237,0.2);border-radius:16px;
                    padding:20px 24px;transition:all 0.3s ease">
            <p style="color:#94A3B8;font-size:0.8rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:1px;margin:0 0 4px 0">Nastawienie</p>
            <p style="font-size:1.8rem;font-weight:800;margin:0;color:#E2E8F0">
                {emoji_icon}&nbsp;{emoji_label}
            </p>
        </div>
    """)

    cur  = player_stats.get('current', 0)
    price = game_info.get('price', 'Brak danych') if game_info else 'Brak danych'
    col_s3.metric("Graczy online 🎮", f"{cur:,}" if cur else "—")
    col_s4.metric("Cena gry 💰", price)
    
    # Podsumowanie tekstowe
    if percent_pos >= 80:
        summary_text = "Gracze w zdecydowanej większości polecają grę, chwaląc jej zawartość."
    elif percent_pos >= 70:
        summary_text = "Gra spotyka się z ogólnie ciepłym przyjęciem, mimo drobnych uwag."
    elif percent_pos >= 40:
        summary_text = "Opinie społeczności są mocno podzielone, gra wymaga poprawek."
    else:
        summary_text = "Gra boryka się z poważną krytyką ze strony społeczności."
    
    st.info(f"**Podsumowanie nastrojów:** {summary_text}")

    # ── WYKRES 1: Stosunek recenzji (duży, pionowy) ───────────────
    st.markdown("**Stosunek recenzji:**")
    ratio_df = pd.DataFrame({
        'Typ': ['👍 Pozytywne', '👎 Negatywne'],
        'Procent (%)': [percent_pos, 100 - percent_pos],
        'Kolor': ['#22C55E', '#EF4444'],
    })
    ratio_chart = (
        alt.Chart(ratio_df)
        .mark_bar(cornerRadiusEnd=6)
        .encode(
            y=alt.Y('Typ:N', sort=None, title=None,
                    axis=alt.Axis(labelFontSize=15, labelFontWeight='bold')),
            x=alt.X('Procent (%):Q', scale=alt.Scale(domain=[0, 100]),
                    title='Procent (%)',
                    axis=alt.Axis(labelFontSize=12)),
            color=alt.Color('Kolor:N', scale=None, legend=None),
            tooltip=['Typ', alt.Tooltip('Procent (%):Q', format='.1f')],
        )
        .properties(height=180)
    )
    # Etykiety wartości na słupkach
    ratio_text = (
        alt.Chart(ratio_df)
        .mark_text(align='left', dx=6, fontSize=14, fontWeight='bold', color='#E2E8F0')
        .encode(
            y=alt.Y('Typ:N', sort=None),
            x=alt.X('Procent (%):Q'),
            text=alt.Text('Procent (%):Q', format='.1f'),
        )
    )
    st.altair_chart((ratio_chart + ratio_text).configure_view(strokeWidth=0)
                    .configure_axis(grid=False, domainColor='#334155', tickColor='#334155')
                    .configure_mark(opacity=0.95),
                    use_container_width=True)

    # ── TENDENCJA: karty z projekcją na 7 i 30 dni ───────────────
    st.markdown("**Tendencja — prognoza % pozytywnych recenzji:**")

    # Pobierz newsy raz (cached w session_state)
    if 'steam_news' not in st.session_state:
        st.session_state.steam_news = fetch_steam_news(appid) if appid else []
    news_items = st.session_state.steam_news
    devlogs    = [n for n in news_items if n['is_devlog']]

    # Oblicz slope na bazie devlogów i trendu lokalnych recenzji
    today = datetime.now().date()
    last_devlog_date = None
    if devlogs:
        try:
            last_devlog_date = datetime.utcfromtimestamp(devlogs[0]['date']).date()
        except Exception:
            pass
    days_since_devlog = (today - last_devlog_date).days if last_devlog_date else 999
    devlogs_14d = 0
    for dv in devlogs:
        try:
            if (today - datetime.utcfromtimestamp(dv['date']).date()).days <= 14:
                devlogs_14d += 1
        except Exception:
            pass
    slope = 0.05
    if   days_since_devlog <= 7:   slope += 0.08
    elif days_since_devlog <= 14:  slope += 0.04
    elif days_since_devlog <= 30:  slope += 0.01
    elif days_since_devlog > 60:   slope -= 0.05
    if devlogs_14d >= 2: slope += 0.03
    r10, r20 = local_reviews[:10], local_reviews[10:20]
    if r10 and r20:
        rt = sum(1 for x in r10 if x.get('sentiment') == 'positive') / len(r10) * 100
        ro = sum(1 for x in r20 if x.get('sentiment') == 'positive') / len(r20) * 100
        if   rt > ro + 5:  slope += 0.05
        elif rt < ro - 5:  slope -= 0.05
    slope = max(-0.2, min(0.3, slope))

    proj_7d  = slope * 7
    proj_30d = slope * 30

    def _delta_str(val):
        return f"+{val:.1f}%" if val >= 0 else f"{val:.1f}%"

    pt1, pt2, pt3 = st.columns(3)
    pt1.metric("Prognoza — 7 dni",  _delta_str(proj_7d),
               delta=f"slope {slope:+.2f}%/dzień", delta_color='normal')
    pt2.metric("Prognoza — 30 dni", _delta_str(proj_30d))
    devlog_info = str(last_devlog_date) if last_devlog_date else "brak danych"
    pt3.metric("Ostatni devlog", devlog_info)
    if last_devlog_date:
        st.caption(f"📜 \"{devlogs[0]['title']}\" — {days_since_devlog} dni temu")

    # ── ANALIZA SKARG I DEVLOGÓW ──────────────────────────────────
    st.html('<div class="gradient-divider"></div>')
    st.markdown("### 📋 Analiza skarg graczy od ostatniego devloga")

    TOPICS = {
        '🐛 Bugi / Błędy':       ['bug', 'crash', 'błąd', 'glitch', 'freeze', 'frozen',
                                   'stuck', 'broken', 'zepsut', 'nie działa', 'crashes'],
        '⚡ Wydajność / FPS':    ['fps', 'lag', 'laguje', 'performance', 'optimization',
                                   'stutter', 'slow', 'wolno', 'klatki', 'optymalizacja'],
        '💰 Cena / Wartość':     ['cena', 'drogo', 'drogi', 'drogie', 'price', 'expensive',
                                   'overpriced', 'refund', 'zwrot', 'worth', 'money'],
        '📦 Mało treści':        ['za krótk', 'krótk', 'pust', 'nud', 'short', 'empty',
                                   'boring', 'repetitiv', 'mało treści', 'content'],
        '🔧 Brakujące funkcje':  ['brak', 'brakuje', 'missing', 'removed', 'feature',
                                   'funkcja', 'opcja', 'ustawienia', 'option', 'setting'],
        '🛠️ Aktualizacje':       ['update', 'aktualizacja', 'fix', 'napraw', 'support',
                                   'ignored', 'porzucony', 'dead', 'abandoned'],
        '🖥️ Optymalizacja PC':   ['ram', 'memory', 'gpu', 'cpu', 'wymaga', 'specs',
                                   'requirements', 'optimize'],
    }

    def count_topics(reviews):
        counts = {}
        for rev in reviews:
            txt = ((rev.get('content_trans') or '') + ' ' + (rev.get('content_orig') or '')).lower()
            for topic, kws in TOPICS.items():
                if any(kw in txt for kw in kws):
                    counts[topic] = counts.get(topic, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    neg_all  = [r for r in local_reviews if r.get('sentiment') == 'negative']

    # Podział: od ostatniego devloga vs. starsze
    last_devlog_date2 = None
    if devlogs:
        try:
            last_devlog_date2 = datetime.utcfromtimestamp(devlogs[0]['date']).date()
        except Exception:
            pass
    if last_devlog_date2:
        neg_recent = [r for r in neg_all if _parse_rev_date(r, datetime.now().date()) >= last_devlog_date2]
        neg_old    = [r for r in neg_all if _parse_rev_date(r, datetime.now().date()) <  last_devlog_date2]
    else:
        split = max(1, len(neg_all) * 2 // 3)
        neg_recent = neg_all[:len(neg_all) - split]
        neg_old    = neg_all[len(neg_all) - split:]

    counts_all    = count_topics(neg_all)
    counts_recent = count_topics(neg_recent)
    counts_old    = count_topics(neg_old)

    # Rozwiązane = recenzje, które zmieniły sentyment z negatywnego na pozytywny,
    # albo pozytywne, na które odpowiedział deweloper
    resolved_reviews = [
        r for r in local_reviews 
        if r.get('sentiment') == 'positive' and 
        (r.get('developer_response') or r.get('timestamp_updated'))
    ]
    resolved_counts = count_topics(resolved_reviews)

    def render_topic_bar(counts, total, color):
        if not counts:
            st.caption("Brak danych")
            return
        for topic, cnt in list(counts.items())[:5]:
            pct = cnt / max(total, 1) * 100
            st.html(f"""
            <div style="margin:6px 0">
              <div style="display:flex;justify-content:space-between;
                          font-size:0.82rem;color:#CBD5E1;margin-bottom:3px">
                <span>{topic}</span><span>{cnt} recenzji</span>
              </div>
              <div style="background:#1E293B;border-radius:6px;height:8px">
                <div style="width:{pct:.0f}%;background:{color};
                            height:8px;border-radius:6px"></div>
              </div>
            </div>""")

    label_since = f"od {last_devlog_date2}" if last_devlog_date2 else "ostatnie ⅓"
    n2 = len(neg_recent)
    st.markdown(f"**Nierozwiązane problemy** *({label_since}, n={n2})*")
    render_topic_bar(counts_recent, n2, '#F59E0B')

    # Devlogi timeline
    if devlogs:
        st.markdown("**📰 Ostatnie devlogi / aktualizacje:**")
        for d in devlogs[:5]:
            try:
                d_date = datetime.utcfromtimestamp(d['date']).strftime('%d %b %Y')
            except Exception:
                d_date = '?'
            
            st.markdown(f"- `{d_date}` — [{d['title']}]({d['url']})")

st.html('<div class="gradient-divider"></div>')

# ── FILTRY RECENZJI ──────────────────────────────────────────────
st.write(f"**Aktywny filtr:** {'Wszystkie' if st.session_state.active_sentiment == 'all' else 'Pozytywne' if st.session_state.active_sentiment == 'positive' else 'Negatywne'}")

if st.button(f"WSZYSTKIE RECENZJE STEAM ({total_revs})", use_container_width=True, type="primary" if st.session_state.active_sentiment == 'all' else "secondary"):
    st.session_state.active_sentiment = 'all'
    st.rerun()
    
c1, c2 = st.columns(2)
with c1:
    if st.button(f"👍 Pozytywne ({total_pos})", use_container_width=True, type="primary" if st.session_state.active_sentiment == 'positive' else "secondary"):
        st.session_state.active_sentiment = 'positive'
        st.rerun()
with c2:
    if st.button(f"👎 Negatywne ({total_neg})", use_container_width=True, type="primary" if st.session_state.active_sentiment == 'negative' else "secondary"):
        st.session_state.active_sentiment = 'negative'
        st.rerun()

st.html('<div class="gradient-divider"></div>')


# ── RENDEROWANIE KARTY ───────────────────────────────────────────
def render_item_card(item: dict):
    """Renderuje pojedynczą kartę recenzji."""
    item_id = item.get('id', 'unknown')
    sentiment = item.get('sentiment', 'neutral')

    if sentiment == 'positive':
        card_key = f"card_pos_{item_id}"
        badge = "👍 POZYTYWNA"
    else:
        card_key = f"card_neg_{item_id}"
        badge = "👎 NEGATYWNA"

    with st.container(key=card_key):
        author = item.get('author', 'Anonim')
        st.caption(f"**{badge}** · {author}")

        title = item.get('title', 'Bez tytułu')
        st.markdown(f"**{title}**")

        trans = item.get('content_trans', '')
        if trans:
            display = trans if len(trans) < 500 else trans[:500] + "…"
            st.info(f"🌐 **Tłumaczenie PL:**\n\n{display}", icon="🌐")

        orig = item.get('content_orig', '')
        if orig:
            with st.expander("📄 Oryginalny tekst"):
                st.markdown(orig)

        url = item.get('url', '')
        if url:
            st.link_button("🔗 Odpowiedz na Steam", url)


# ── LISTA RECENZJI ───────────────────────────────────────────────
active_items = get_items(0, appid)

if not active_items:
    st.markdown("### 🎉 Wszystko załatwione!")
    st.write("Brak recenzji w bazie. Kliknij **🔄 Pobierz nowe dane**.")
else:
    # Filtrowanie
    filtered = [i for i in active_items if i['type'] == 'Recenzja']
    if st.session_state.active_sentiment == 'positive':
        filtered = [i for i in filtered if i.get('sentiment') == 'positive']
    elif st.session_state.active_sentiment == 'negative':
        filtered = [i for i in filtered if i.get('sentiment') == 'negative']

    st.html('<div class="gradient-divider"></div>')

    if 'display_limit' not in st.session_state:
        st.session_state.display_limit = 20

    filtered_to_display = filtered[:st.session_state.display_limit]

    for item in filtered_to_display:
        render_item_card(item)

    if st.session_state.display_limit < len(filtered):
        if st.button("🔽 Pokaż więcej (20)", use_container_width=True):
            st.session_state.display_limit += 20
            st.rerun()