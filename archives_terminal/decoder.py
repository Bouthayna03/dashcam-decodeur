import hashlib
import os
import sys
from supabase import create_client

# --- CONFIGURATION ---
# 1. URL avec le Slash à la fin
url = "https://zofarlcgqjhpdfzjtnit.supabase.co/"

# 2. TA CLÉ SERVICE_ROLE (Clé Admin)
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZmFybGNncWpocGRmemp0bml0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzIwMjE4MCwiZXhwIjoyMDgyNzc4MTgwfQ.48TQnioeyJkrDxDH0MpYb85u3fkyOjOM2dMk1D8Ao8g"

# Initialisation
try:
    supabase = create_client(url, key)
    # Pas de print ici pour garder la sortie propre si on veut juste le résultat
except Exception as e:
    print(f"❌ Erreur connexion : {e}")
    exit()

dossier_verification = "verif_temp"
if not os.path.exists(dossier_verification):
    os.makedirs(dossier_verification)

def calculer_hash(fichier_path):
    sha256 = hashlib.sha256()
    with open(fichier_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def verifier_une_video(target_name):
    """Vérifie UNE SEULE vidéo spécifique"""
    print(f"\n🎯 VÉRIFICATION CIBLÉE : {target_name}")
    print("=" * 50)

    try:
        # 1. Chercher le hash dans la DB
        response = supabase.table("logs").select("*").eq("filename", target_name).execute()
        
        if len(response.data) == 0:
            print(f"❌ ERREUR : Cette vidéo n'existe pas dans le registre (Logs).")
            print("   -> Ce fichier est peut-être une invention totale ou a été supprimé.")
            return

        preuve = response.data[0]
        hash_attendu = preuve['hash']
        print(f"📄 Preuve juridique trouvée (Date : {preuve['created_at']})")
        print(f"🔐 Hash officiel : {hash_attendu}")

        # 2. Télécharger le fichier
        chemin_local = os.path.join(dossier_verification, target_name)
        print(f"📥 Téléchargement depuis le Cloud...", end="\r")
        
        try:
            data = supabase.storage.from_("videos").download(target_name)
            with open(chemin_local, 'wb') as f:
                f.write(data)
            print("📥 Téléchargement terminé.             ")
        except Exception as e:
            print(f"❌ ERREUR STORAGE : Impossible de télécharger le fichier.")
            print(f"   -> Le fichier physique a disparu (Nettoyage ou Suppression manuelle).")
            return

        # 3. Vérifier l'intégrité
        hash_trouve = calculer_hash(chemin_local)
        print(f"🔍 Hash du fichier : {hash_trouve}")

        print("-" * 50)
        if hash_trouve == hash_attendu:
            print("✅ RÉSULTAT : AUTHENTIQUE")
            print("   Le fichier est certifié conforme à l'original.")
        else:
            print("⛔ RÉSULTAT : FALSIFICATION DÉTECTÉE")
            print("   Attention : Le contenu de la vidéo a été modifié !")
        
        # Nettoyage
        if os.path.exists(chemin_local):
            os.remove(chemin_local)

    except Exception as e:
        print(f"❌ Erreur système : {e}")
    print("\n")

def verifier_tout():
    """Vérifie TOUTES les vidéos présentes"""
    print("🕵️‍♂️ --- AUDIT GLOBAL DU SYSTÈME ---")
    
    response = supabase.table("logs").select("*").order('created_at', desc=True).execute()
    logs = response.data
    
    if not logs:
        print("Aucun enregistrement.")
        return

    print(f"Analyse de {len(logs)} preuves...\n")
    
    for log in logs:
        verifier_une_video(log['filename'])

# --- POINT D'ENTRÉE ---
if __name__ == "__main__":
    # Si on donne un argument (ex: python decoder.py video_123.mp4)
    if len(sys.argv) > 1:
        nom_fichier = sys.argv[1]
        verifier_une_video(nom_fichier)
    else:
        # Sinon on lance tout
        verifier_tout()