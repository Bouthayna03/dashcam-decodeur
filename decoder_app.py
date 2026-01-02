import streamlit as st
import hashlib
import os
import tempfile
import time
from supabase import create_client
from PIL import Image

# --- CONFIGURATION DES CHEMINS ---
DOSSIER_ICONES = "icons"

def get_icon_path(nom_fichier):
    return os.path.join(DOSSIER_ICONES, nom_fichier)

# --- FONCTION DE SÉCURITÉ ---
def charger_image_page(nom_fichier, emoji_fallback):
    chemin = get_icon_path(nom_fichier)
    try:
        return Image.open(chemin)
    except:
        return emoji_fallback

# --- CONFIGURATION DE LA PAGE ---
icon_browser = charger_image_page("logo.png", "🛡️")

st.set_page_config(
    page_title="Dashcam Security Hub",
    page_icon=icon_browser,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- TES CLÉS ---
URL = "https://zofarlcgqjhpdfzjtnit.supabase.co/"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZmFybGNncWpocGRmemp0bml0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzIwMjE4MCwiZXhwIjoyMDgyNzc4MTgwfQ.48TQnioeyJkrDxDH0MpYb85u3fkyOjOM2dMk1D8Ao8g"

# --- STYLE CSS "COMPACT" (Pour gagner de la place verticale) ---
st.markdown("""
<style>
    /* 1. On remonte tout le contenu au maximum */
    .block-container {
        padding-top: 2rem !important; 
        padding-bottom: 0rem !important;
    }

    /* 2. On réduit l'espace entre les éléments (Titre, Metrics, Tabs) */
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem !important; /* Réduit l'espace vide entre les blocs */
    }

    /* 3. Sidebar compacte */
    [data-testid="stSidebarUserContent"] {
        padding-top: 2rem !important;
    }

    /* Styles Généraux */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem; /* Un peu plus petit pour gagner de la place */
        color: #0e1117;
    }
    video {
        width: 100% !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
@st.cache_resource
def init_supabase():
    try:
        return create_client(URL, KEY)
    except Exception as e:
        return None

def calculer_hash(fichier_path):
    sha256 = hashlib.sha256()
    with open(fichier_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def afficher_icone(nom_fichier, emoji_fallback, largeur=40):
    chemin = get_icon_path(nom_fichier)
    try:
        if os.path.exists(chemin):
            img = Image.open(chemin)
            st.image(img, width=largeur)
        else:
            st.markdown(f"## {emoji_fallback}")
    except:
        st.markdown(f"## {emoji_fallback}")

# --- INITIALISATION ---
supabase = init_supabase()

if not supabase:
    st.error("❌ Erreur critique : Impossible de se connecter au Cloud sécurisé.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    afficher_icone("admin.png", "👤", largeur=100)
    
    st.markdown("### Admin Panel")
    st.caption("Système de certification vidéo")
    st.divider()
    
    st.markdown("### 📡 État du Système")
    st.success("Cloud : Connecté (Online)")
    st.info("Mode : Administrateur")
    
    st.divider()
    if st.button("🔄 Rafraîchir les données"):
        st.rerun()
    st.markdown("---")
    st.caption("Projet Dashcam Cloud © 2026")

# --- RÉCUPÉRATION DES DONNÉES ---
try:
    response = supabase.table("logs").select("*").order('created_at', desc=True).execute()
    logs = response.data
    total_videos = len(logs)
except Exception as e:
    st.error(f"Erreur de lecture DB : {e}")
    st.stop()

# --- ENTÊTE PRINCIPAL ---
c_logo, c_text = st.columns([1, 10], vertical_alignment="center")

with c_logo:
    afficher_icone("logo.png", "🛡️", largeur=80)

with c_text:
    st.markdown("""
        <h1 style='padding: 0; margin: 0; margin-bottom: 0px;'>
            Centre de Contrôle d'Intégrité
        </h1>
        """, unsafe_allow_html=True)

st.write("") 
st.markdown(f"Bienvenue dans l'interface de vérification. Il y a actuellement **{total_videos} preuves** sécurisées dans le registre sécurisé.")

# --- ONGLETS ---
tab1, tab2 = st.tabs(["📂 Vérification Unitaire", "🚀 Vérification Globale"])

# =========================================================
# ONGLET 1 : VUE DÉTAILLÉE (AVEC SCROLL FIXÉ)
# =========================================================
with tab1:
    # 1. PARTIE FIXE (KPIs)
    col1, col2 = st.columns(2)
    col1.metric("Vidéos Stockées", f"{total_videos}", "Fichiers")
    col2.metric("Statut Sécurité", "Actif", delta="OK", delta_color="normal")
    st.divider()
    
    if not logs:
        st.warning("Aucune donnée disponible.")
    else:
        # 2. PARTIE DÉFILANTE (Zone scrollable)
        # --- MODIFICATION CLÉ : Hauteur réduite à 400px ---
        # Cela force la création d'une petite fenêtre de scroll interne.
        # Si ton écran est petit, 400px garantit que ça ne dépasse pas en bas.
        with st.container(height=400, border=False):
            
            for index, preuve in enumerate(logs):
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        with st.expander(f"📁 Fichier : {preuve['filename']}"):
                            col_gauche, col_droite = st.columns([1.5, 1])
                            with col_gauche:
                                c_ico_f, c_txt_f = st.columns([1, 5])
                                with c_ico_f:
                                    afficher_icone("fichier.png", "📄", largeur=40)
                                with c_txt_f:
                                    st.markdown("**Empreinte Numérique (Hash) :**")
                                    st.code(preuve['hash'], language='text')
                                
                                st.write("") 
                                bouton_clique = st.button(f"🔍 Auditer cette vidéo", key=f"btn_{preuve['id']}")

                            if bouton_clique:
                                with st.spinner("Analyse cryptographique..."):
                                    try:
                                        data = supabase.storage.from_("videos").download(preuve['filename'])
                                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                                            tmp.write(data)
                                            path = tmp.name
                                        
                                        h = calculer_hash(path)
                                        os.remove(path)
                                        
                                        if h == preuve['hash']:
                                            with col_gauche:
                                                st.divider()
                                                sub_c1, sub_c2 = st.columns([1, 4])
                                                with sub_c1:
                                                    afficher_icone("valide.png", "✅", largeur=50)
                                                with sub_c2:
                                                    st.success("AUTHENTIQUE")
                                                    st.caption("Signature certifiée conforme")
                                                st.balloons()
                                            with col_droite:
                                                st.caption("🎬 Preuve visuelle")
                                                st.video(data) 
                                        else:
                                            with col_gauche:
                                                st.divider()
                                                sub_c1, sub_c2 = st.columns([1, 4])
                                                with sub_c1:
                                                    afficher_icone("echec.png", "❌", largeur=50)
                                                with sub_c2:
                                                    st.error("FALSIFICATION")
                                                    st.caption("Le Hash ne correspond pas !")
                                    except Exception as e:
                                        with col_gauche:
                                            st.error("⚠️ Erreur : Fichier introuvable.")
                    with c2:
                        st.caption(f"ID: {preuve['id']}")
                        st.caption("Type: MP4/H.264")

# =========================================================
# ONGLET 2 : AUDIT GLOBAL
# =========================================================
with tab2:
    st.header("⚡ Audit de Masse")
    st.write("Ce module vérifie l'intégrité de toute la base de données.")
    
    col_audit, col_res = st.columns([1, 2])
    with col_audit:
        st.info(f"Vidéos à traiter : {total_videos}")
        lancer_audit = st.button("▶️ LANCER L'AUDIT COMPLET", type="primary")

    if lancer_audit:
        valid_count = 0
        error_count = 0
        missing_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.divider()
        # Pour l'audit global aussi, on fixe la hauteur
        with st.container():
            for i, preuve in enumerate(logs):
                status_text.text(f"Traitement de {preuve['filename']} ({i+1}/{total_videos})...")
                progress_bar.progress((i + 1) / total_videos)
                try:
                    data = supabase.storage.from_("videos").download(preuve['filename'])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                        tmp.write(data)
                        path = tmp.name
                    h_now = calculer_hash(path)
                    os.remove(path)
                    
                    if h_now == preuve['hash']:
                        valid_count += 1
                        st.toast(f"✅ {preuve['filename']} OK") 
                    else:
                        error_count += 1
                        st.error(f"❌ {preuve['filename']} : FALSIFIÉ !")
                except Exception:
                    missing_count += 1
                    st.warning(f"⚠️ {preuve['filename']} : MANQUANT")
                time.sleep(0.1)

        progress_bar.empty()
        status_text.empty()
      
        
        if error_count == 0 and missing_count == 0:
            c_icon, c_txt = st.columns([1, 8])
            with c_icon:
                afficher_icone("valide.png", "✨", largeur=80)
            with c_txt:
                st.success("### INTÉGRITÉ DU SYSTÈME : 100% PARFAITE")
                st.write("Toutes les preuves sont authentiques.")
            st.balloons()
        else:
            c_icon, c_txt = st.columns([1, 8])
            with c_icon:
                afficher_icone("echec.png", "⚠️", largeur=80)
            with c_txt:
                st.warning("### ANOMALIES DÉTECTÉES")
                st.write("Certains fichiers sont corrompus ou manquants.")

        st.write("")
        c_val, c_err, c_miss = st.columns(3)
        c_val.metric("Authentiques", valid_count, "Vidéos")
        c_err.metric("Falsifiées", error_count, "Alertes", delta_color="inverse")
        c_miss.metric("Introuvables", missing_count, "Fichiers")