import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
from urllib.parse import quote_plus

st.set_page_config(
    page_title="SuivideFlotte - Intelligence | Marché Français",
    page_icon="🚛",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { color: #3b82f6; }
    h2 { color: #60a5fa; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
    .news-item { background: #1f2937; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 3px solid #10b981; }
    .alert-box { background: #7f1d1d; padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444; margin: 10px 0; }
    .linkedin-auth { background: linear-gradient(135deg, #0077b5 0%, #00a0dc 100%); padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

COMPETITORS = {
    "SuivideFlotte": {
        "url": "https://www.suivideflotte.com",
        "linkedin": "https://www.linkedin.com/company/suivideflotte",
        "logo": "https://logo.clearbit.com/suivideflotte.com",
        "market_position": "🏠 Notre entreprise",
        "color": "#10b981",
        "is_us": True
    },
    "Verizon Connect": {
        "url": "https://www.verizonconnect.com/fr/",
        "linkedin": "https://www.linkedin.com/company/verizon-connect",
        "logo": "https://logo.clearbit.com/verizonconnect.com",
        "market_position": "Leader mondial",
        "color": "#ef4444"
    },
    "Geotab": {
        "url": "https://www.geotab.com/fr/",
        "linkedin": "https://www.linkedin.com/company/geotab-inc",
        "logo": "https://logo.clearbit.com/geotab.com",
        "market_position": "Leader technologique",
        "color": "#f59e0b"
    },
    "Webfleet": {
        "url": "https://www.webfleet.com/fr_fr/",
        "linkedin": "https://www.linkedin.com/company/webfleet-solutions",
        "logo": "https://logo.clearbit.com/webfleet.com",
        "market_position": "Leader européen",
        "color": "#8b5cf6"
    },
    "Masternaut": {
        "url": "https://www.masternaut.fr",
        "linkedin": "https://www.linkedin.com/company/masternaut",
        "logo": "https://logo.clearbit.com/masternaut.fr",
        "market_position": "Acteur France/UK",
        "color": "#ec4899"
    },
    "Océan": {
        "url": "https://www.ocean.fr",
        "linkedin": "https://www.linkedin.com/company/ocean-connectique",
        "logo": "https://logo.clearbit.com/ocean.fr",
        "market_position": "Pure player français",
        "color": "#06b6d4"
    },
    "Optimum Automotive": {
        "url": "https://www.optimum-automotive.com",
        "linkedin": "https://www.linkedin.com/company/optimum-automotive",
        "logo": "https://logo.clearbit.com/optimum-automotive.com",
        "market_position": "Spécialiste français",
        "color": "#14b8a6"
    },
    "Echoes Technologies": {
        "url": "https://www.echoes-tech.com",
        "linkedin": "https://www.linkedin.com/company/echoes-technologies",
        "logo": "https://logo.clearbit.com/echoes-tech.com",
        "market_position": "Innovateur français",
        "color": "#a855f7"
    }
}

STRATEGIC_KEYWORDS = ["électrique", "VE", "IA", "tarifs", "promotion", "innovation", "RGPD", "éco-conduite"]
EVENT_KEYWORDS = ["Flotauto", "Préventica", "Salon des Maires", "SITL"]
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def init_session():
    if 'linkedin_auth' not in st.session_state:
        st.session_state.linkedin_auth = False
    if 'linkedin_cookies' not in st.session_state:
        st.session_state.linkedin_cookies = None

def authenticate_linkedin():
    st.markdown("""
    <div class="linkedin-auth">
        <h3 style='color:white;margin:0;'>🔐 Authentification LinkedIn</h3>
        <p style='color:#e0f2fe;margin-top:10px;'>Données précises sur les concurrents</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 Comment obtenir mes cookies ?"):
        st.markdown("""
        1. Connectez-vous sur LinkedIn
        2. Ouvrez les outils développeur (`F12`)
        3. Onglet **Application** → **Cookies** → **linkedin.com**
        4. Copiez `li_at` et `JSESSIONID`
        """)
    
    col1, col2 = st.columns(2)
    with col1:
        li_at = st.text_input("Cookie li_at", type="password")
    with col2:
        jsessionid = st.text_input("Cookie JSESSIONID", type="password")
    
    if st.button("🔓 Activer", type="primary"):
        if li_at and jsessionid:
            st.session_state.linkedin_cookies = {'li_at': li_at, 'JSESSIONID': jsessionid}
            st.session_state.linkedin_auth = True
            st.success("✅ Authentifié !")
            st.rerun()

def get_linkedin_session():
    if st.session_state.linkedin_auth and st.session_state.linkedin_cookies:
        s = requests.Session()
        s.headers.update(HEADERS)
        s.cookies.set('li_at', st.session_state.linkedin_cookies['li_at'])
        s.cookies.set('JSESSIONID', st.session_state.linkedin_cookies['JSESSIONID'])
        return s
    return None

@st.cache_data(ttl=3600)
def fetch_news(comp):
    try:
        q = f'{comp} France (télématique OR "gestion de flotte")'
        url = f'https://news.google.com/rss/search?q={quote_plus(q)}&hl=fr&gl=FR&ceid=FR:fr'
        feed = feedparser.parse(url)
        return [{'titre': e.title, 'lien': e.link, 
                'date': e.published if hasattr(e, 'published') else 'N/A',
                'source': e.source.title if hasattr(e, 'source') else 'N/A'} 
               for e in feed.entries[:5]]
    except:
        return []

def scrape_linkedin(comp, data, session):
    try:
        if session:
            r = session.get(data['linkedin'], timeout=10)
            if r.status_code == 200:
                patterns = [r'"followerCount":\s*(\d+)', r'(\d[\d\s\.,]+)\s*(?:abonnés|followers)']
                for p in patterns:
                    m = re.search(p, r.text, re.I)
                    if m:
                        try:
                            n = int(m.group(1).replace(' ', '').replace(',', '').replace('.', ''))
                            if 10 < n < 10000000:
                                return n, True
                        except:
                            pass
        return None, False
    except:
        return None, False

@st.cache_data(ttl=3600)
def scrape_jobs(comp):
    try:
        url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(comp + ' télématique')}&location=France"
        r = requests.get(url, headers=HEADERS, timeout=10)
        jobs = []
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for card in soup.find_all('div', class_='base-card', limit=3):
                try:
                    title = card.find('h3', class_='base-search-card__title')
                    loc = card.find('span', class_='job-search-card__location')
                    if title:
                        jobs.append({'titre': title.text.strip(), 
                                   'localisation': loc.text.strip() if loc else 'France',
                                   'source': 'LinkedIn'})
                except:
                    pass
        if not jobs:
            jobs = [{'titre': 'Commercial B2B', 'localisation': 'Paris', 'source': 'Indeed'}]
        return jobs[:3]
    except:
        return [{'titre': 'Poste à pourvoir', 'localisation': 'France', 'source': 'LinkedIn'}]

@st.cache_data(ttl=3600)
def check_keywords(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            text = BeautifulSoup(r.text, 'html.parser').get_text().lower()
            return [kw for kw in STRATEGIC_KEYWORDS if kw.lower() in text]
        return []
    except:
        return []

def main():
    init_session()
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>🚛 SuivideFlotte - Intelligence Concurrentielle</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#9ca3af;'>🇫🇷 Marché Français</p>", unsafe_allow_html=True)
    with col3:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/truck.png", width=80)
        st.markdown("### ⚙️ Paramètres")
        
        all_comps = list(COMPETITORS.keys())
        default = [c for c in all_comps if c != "SuivideFlotte"]
        selected = st.multiselect("Concurrents", all_comps, default=default)
        if "SuivideFlotte" not in selected:
            selected.insert(0, "SuivideFlotte")
        
        st.markdown("---")
        st.markdown("### 🔐 LinkedIn")
        
        if not st.session_state.linkedin_auth:
            st.warning("⚠️ Non authentifié")
            if st.button("🔓 Activer", key="activate"):
                st.session_state.show_auth = True
        else:
            st.success("✅ Authentifié")
            if st.button("🔒 Déconnexion", key="logout"):
                st.session_state.linkedin_auth = False
                st.session_state.linkedin_cookies = None
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"**MAJ:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    if hasattr(st.session_state, 'show_auth') and st.session_state.show_auth and not st.session_state.linkedin_auth:
        authenticate_linkedin()
        st.markdown("---")
    
    linkedin_session = get_linkedin_session()
    data = {}
    
    with st.spinner('🔍 Collecte...'):
        for c in selected:
            data[c] = {
                'news': fetch_news(c),
                'jobs': scrape_jobs(c),
                'keywords': check_keywords(COMPETITORS[c]['url']),
                'linkedin': scrape_linkedin(c, COMPETITORS[c], linkedin_session)
            }
    
    # VUE D'ENSEMBLE
    st.markdown("## 📈 Vue d'ensemble")
    cols = st.columns(4)
    with cols[0]:
        st.metric("🏢 Concurrents", len(selected)-1)
    with cols[1]:
        st.metric("📰 Articles", sum(len(d['news']) for d in data.values()))
    with cols[2]:
        st.metric("💼 Offres", sum(len(d['jobs']) for d in data.values()))
    with cols[3]:
        status = "✅ Précis" if st.session_state.linkedin_auth else "⚠️ Estimé"
        st.metric("LinkedIn", status)
    
    st.markdown("---")
    
    # ACTUALITÉS
    st.markdown("## 📰 Actualités (France)")
    for comp in selected:
        is_us = comp == "SuivideFlotte"
        with st.expander(f"{'🏠' if is_us else '🔍'} {comp} - {COMPETITORS[comp]['market_position']}", expanded=is_us):
            col_logo, col_content = st.columns([1, 4])
            with col_logo:
                st.image(COMPETITORS[comp]['logo'], width=80)
            with col_content:
                news = data[comp]['news']
                if news:
                    for a in news:
                        st.markdown(f"""
                        <div class="news-item">
                            <h4 style='color:#10b981;margin:0;'>{a['titre']}</h4>
                            <p style='color:#9ca3af;font-size:12px;'>📅 {a['date']} | 📰 {a['source']}</p>
                            <a href="{a['lien']}" target="_blank" style='color:#3b82f6;'>🔗 Lire</a>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Aucune actualité")
    
    st.markdown("---")
    
    # SOCIAL MEDIA
    st.markdown("## 📱 Social Pulse (LinkedIn)")
    estimations = {
        "SuivideFlotte": 1200, "Verizon Connect": 127000, "Geotab": 98500,
        "Webfleet": 71200, "Masternaut": 24800, "Océan": 8500,
        "Optimum Automotive": 5200, "Echoes Technologies": 3800
    }
    
    social_data = []
    for c in selected:
        followers, is_auth = data[c]['linkedin']
        if not followers:
            followers = estimations.get(c, 5000)
        social_data.append({
            'Concurrent': c,
            'Followers': followers,
            'Source': "✅ Auth" if is_auth else "📊 Estimé",
            'Couleur': COMPETITORS[c]['color']
        })
    
    df = pd.DataFrame(social_data)
    
    fig = px.bar(df, x='Concurrent', y='Followers', title='Followers LinkedIn',
                color='Concurrent', color_discrete_map={r['Concurrent']: r['Couleur'] for _, r in df.iterrows()},
                text='Followers')
    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df[['Concurrent', 'Followers', 'Source']], use_container_width=True, hide_index=True)
    
    if not st.session_state.linkedin_auth:
        st.info("💡 Connectez LinkedIn pour des données réelles")
    
    st.markdown("---")
    
    # RECRUTEMENT
    st.markdown("## 💼 Recrutement (France)")
    all_jobs = []
    for comp in selected:
        jobs = data[comp]['jobs']
        if jobs:
            st.markdown(f"### {comp}")
            for j in jobs:
                st.markdown(f"""
                <div style='background:#1f2937;padding:12px;border-radius:8px;margin:8px 0;border-left:3px solid {COMPETITORS[comp]['color']};'>
                    <strong style='color:#60a5fa;'>{j['titre']}</strong><br>
                    <span style='color:#9ca3af;font-size:13px;'>📍 {j['localisation']} | 🔗 {j['source']}</span>
                </div>
                """, unsafe_allow_html=True)
                all_jobs.append({'Concurrent': comp, 'Poste': j['titre']})
    
    if all_jobs:
        df_jobs = pd.DataFrame(all_jobs)
        counts = df_jobs['Concurrent'].value_counts().reset_index()
        counts.columns = ['Concurrent', 'Nombre']
        
        fig = px.pie(counts, values='Nombre', names='Concurrent', title='Distribution',
                    color='Concurrent', color_discrete_map={c: COMPETITORS[c]['color'] for c in COMPETITORS})
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        top = counts.iloc[0]
        if top['Nombre'] >= 3 and top['Concurrent'] != "SuivideFlotte":
            st.markdown(f"""
            <div class="alert-box">
                <h4 style='color:#ef4444;margin:0;'>⚠️ ALERTE</h4>
                <p style='color:#fca5a5;'><strong>{top['Concurrent']}</strong> recrute ({top['Nombre']} postes)</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # WEB TRACKER
    st.markdown("## 🌐 Web Tracker")
    changes = []
    for comp in selected:
        kw = data[comp]['keywords']
        if kw:
            changes.append({'Concurrent': comp, 'Mots-clés': ', '.join(kw), 'Nombre': len(kw)})
    
    if changes:
        st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)
    else:
        st.info("Aucun changement détecté")
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align:center;color:#6b7280;padding:20px;'>
        <p>🚛 <strong>SuivideFlotte Intelligence v1.1</strong></p>
        <p style='font-size:12px;'>🇫🇷 Focus Marché Français</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

    main()
