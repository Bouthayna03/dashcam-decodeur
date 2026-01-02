import cv2 
import time
import os
import hashlib 
from supabase import create_client, Client

# --- CONFIGURATION ---
url = "https://zofarlcgqjhpdfzjtnit.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZmFybGNncWpocGRmemp0bml0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcyMDIxODAsImV4cCI6MjA4Mjc3ODE4MH0.Ht3KVad71-nBk3RtlEb0elvFPR5AhQ9Au3q4ZlhKQw0" 

# --- PARAMÈTRES VIDÉO ---
DUREE_SEGMENT = 10
FPS = 20
FRAMES_PAR_SEGMENT = DUREE_SEGMENT * FPS

# --- INITIALISATION ---
try:
    supabase = create_client(url, key)
    print("✅ Connexion Supabase OK")
except Exception as e:
    print(f"❌ Erreur init Supabase: {e}")
    exit()

# Dossier pour le mode hors-ligne
dossier_buffer = "buffer_local"
if not os.path.exists(dossier_buffer):
    os.makedirs(dossier_buffer)

# Dossier temporaire pour créer les vidéos
dossier_temp = "temp_videos"
if not os.path.exists(dossier_temp):
    os.makedirs(dossier_temp)

cap = cv2.VideoCapture(0) 

# Récupérer les dimensions de la caméra
largeur = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
hauteur = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"📷 Résolution caméra : {largeur}x{hauteur}")

def calculer_hash(fichier_path):
    """Calcule le hash SHA256 d'un fichier"""
    sha256 = hashlib.sha256()
    with open(fichier_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def envoyer_vers_cloud(chemin_video, nom_fichier, signature):
    """
    Envoie la vidéo vers Supabase de manière ATOMIQUE
    Storage + Database doivent TOUS LES DEUX réussir
    """
    try:
        print(f"   📤 Envoi vers le cloud...", end="\r")
        
        # ÉTAPE 1 : Vérifier si le log existe déjà
        existing_log = supabase.table("logs").select("id").eq("filename", nom_fichier).execute()
        
        if len(existing_log.data) > 0:
            # Le log existe déjà → La vidéo a déjà été traitée
            print(f"   ✅ Déjà synchronisé : {nom_fichier}                    ")
            # On supprime le fichier local car c'est un doublon
            if os.path.exists(chemin_video):
                os.remove(chemin_video)
            return True
        
        # ÉTAPE 2 : Upload du fichier vidéo
        extension = nom_fichier.split('.')[-1]
        content_type = {
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo',
            'webm': 'video/webm'
        }.get(extension, 'video/mp4')
        
        with open(chemin_video, 'rb') as f:
            try:
                supabase.storage.from_("videos").upload(
                    path=nom_fichier, 
                    file=f, 
                    file_options={"content-type": content_type}
                )
            except Exception as upload_err:
                # Si erreur 409 (fichier existe), on continue quand même
                if "409" not in str(upload_err) and "Duplicate" not in str(upload_err):
                    # C'est une vraie erreur (réseau, etc.)
                    raise upload_err
                # Sinon on continue, le fichier existe déjà
        
        # ÉTAPE 3 : Enregistrement du hash en base
        data = {"filename": nom_fichier, "hash": signature}
        supabase.table("logs").insert(data).execute()
        
        print(f"   ✅ Cloud OK : {nom_fichier}                    ")
        
        # ÉTAPE 4 : Suppression du fichier local
        if os.path.exists(chemin_video):
            os.remove(chemin_video)
        
        return True
        
    except Exception as e:
        print(f"   ⚠️ Échec envoi : {e}                ")
        return False

def sauvegarder_buffer(chemin_video, nom_fichier):
    """Déplace la vidéo dans le buffer en cas de coupure réseau"""
    destination = os.path.join(dossier_buffer, nom_fichier)
    # Éviter d'écraser si le fichier existe déjà
    if not os.path.exists(destination):
        os.rename(chemin_video, destination)
        print(f"   💾 Sauvegardé en local : {nom_fichier}")
    else:
        # Le fichier existe déjà dans le buffer
        os.remove(chemin_video)

def synchroniser_buffer():
    """Tente de renvoyer les vidéos du buffer vers le cloud"""
    fichiers_buffer = os.listdir(dossier_buffer)
    
    if len(fichiers_buffer) == 0:
        return
    
    print(f"\n🔄 {len(fichiers_buffer)} fichier(s) en attente dans le buffer...")
    
    for nom_fichier in fichiers_buffer:
        chemin_complet = os.path.join(dossier_buffer, nom_fichier)
        
        # Recalculer le hash
        signature = calculer_hash(chemin_complet)
        
        print(f"   🔁 Tentative de renvoi : {nom_fichier}")
        
        if envoyer_vers_cloud(chemin_complet, nom_fichier, signature):
            print(f"   ✅ Synchronisation réussie")
        else:
            print(f"   ⏸️ Toujours en attente...")
            break  # Si un échoue, on arrête

def maintenance_nettoyage():
    """Supprime les vidéos trop anciennes (garde les 5 dernières)"""
    try:
        # 1. On récupère la liste triée par date
        response = supabase.table("logs").select("*").order("created_at", desc=False).execute()
        logs = response.data
        
        # Si on dépasse 5 vidéos, on supprime TOUT ce qui dépasse
        while len(logs) > 5:
            # On prend la plus vieille
            video_a_supprimer = logs[0]
            nom_fichier = video_a_supprimer['filename']
            id_row = video_a_supprimer['id']
            
            print(f"♻️ NETTOYAGE : Suppression de {nom_fichier}...")
            
            # A. Supprimer du storage (Important : utiliser une liste [nom])
            try:
                supabase.storage.from_("videos").remove([nom_fichier])
                print(f"   -> Storage supprimé ✓")
            except Exception as e:
                print(f"   -> Erreur Storage (peut-être déjà vide) : {e}")
            
            # B. Supprimer de la base
            supabase.table("logs").delete().eq("id", id_row).execute()
            print(f"   -> Base de données supprimée ✓")
            
            # On met à jour la liste locale pour la boucle while
            logs.pop(0)
            
    except Exception as e:
        print(f"⚠️ Erreur nettoyage : {e}")

# ========================================
# BOUCLE PRINCIPALE
# ========================================
print("\n🎥 --- DASHCAM EN LIGNE (Mode Vidéo) ---")
print(f"📊 Configuration : {DUREE_SEGMENT}s par segment, {FPS} FPS")
print("   Appuyez sur 'q' pour quitter\n")

compteur_segment = 1

while True:
    timestamp = str(int(time.time()))
    nom_fichier = f"video_{timestamp}.mp4"
    chemin_temp = os.path.join(dossier_temp, nom_fichier)
    
    # Création du VideoWriter
    codecs_a_essayer = [
        ('avc1', 'H.264 (meilleur)'),
        ('H264', 'H.264'),
        ('X264', 'X264'),
        ('mp4v', 'MPEG-4 (fallback)')
    ]
    
    out = None
    for codec, nom in codecs_a_essayer:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(chemin_temp, fourcc, FPS, (largeur, hauteur))
            if out.isOpened():
                if compteur_segment == 1:
                    print(f"   🎬 Codec utilisé : {nom}")
                break
        except:
            continue
    
    if out is None or not out.isOpened():
        print("❌ Impossible de créer le fichier vidéo")
        continue
    
    print(f"\n🎬 SEGMENT {compteur_segment} - Enregistrement de {DUREE_SEGMENT}s...")
    
    # Enregistrement des frames
    for i in range(FRAMES_PAR_SEGMENT):
        ret, frame = cap.read()
        if not ret:
            print("❌ Erreur lecture caméra")
            break
        
        out.write(frame)
        
        # Affichage avec compteur
        texte = f"REC {i+1}/{FRAMES_PAR_SEGMENT}"
        cv2.putText(frame, texte, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Dashcam (Presse 'q' pour quitter)", frame)
        
        # Vérifier si l'utilisateur veut quitter
        if cv2.waitKey(1) & 0xFF == ord('q'):
            out.release()
            os.remove(chemin_temp)
            cap.release()
            cv2.destroyAllWindows()
            print("\n👋 Arrêt de la dashcam")
            exit()
    
    out.release()
    print(f"   ✅ Segment enregistré : {nom_fichier}")
    
    # Calcul du hash
    print(f"   🔐 Calcul du hash...", end="\r")
    signature = calculer_hash(chemin_temp)
    print(f"   🔐 Hash : {signature[:16]}...")
    
    # Tentative d'envoi
    succes = envoyer_vers_cloud(chemin_temp, nom_fichier, signature)
    
    if not succes:
        sauvegarder_buffer(chemin_temp, nom_fichier)
    else:
        # Synchroniser le buffer
        synchroniser_buffer()
        # Nettoyage
        maintenance_nettoyage()
    
    compteur_segment += 1

cap.release()
cv2.destroyAllWindows()