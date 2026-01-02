import os
from supabase import create_client

# --- CONFIGURATION ---
# ATTENTION : Mets bien le slash '/' à la fin de l'URL
url = "https://zofarlcgqjhpdfzjtnit.supabase.co/"

# ICI : Colle ta clé "service_role" (pas la anon !)
key_service_role = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvZmFybGNncWpocGRmemp0bml0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzIwMjE4MCwiZXhwIjoyMDgyNzc4MTgwfQ.48TQnioeyJkrDxDH0MpYb85u3fkyOjOM2dMk1D8Ao8g" 

# On se connecte en mode administrateur
supabase = create_client(url, key_service_role)

print("🕵️‍♂️ --- AUDIT DE VÉRITÉ (MODE ADMIN) ---")

try:
    # 1. Compter les Logs (Base de données)
    response_logs = supabase.table("logs").select("*", count="exact").execute()
    nb_logs = len(response_logs.data)
    print(f"📊 Base de données (Logs) : {nb_logs} enregistrements")

    # 2. Compter les Fichiers (Storage)
    # On liste le contenu du bucket 'videos'
    response_storage = supabase.storage.from_("videos").list()
    
    # Filtrer le dossier vide caché (.emptyFolderPlaceholder)
    fichiers_reels = [f for f in response_storage if f['name'] != '.emptyFolderPlaceholder']
    nb_files = len(fichiers_reels)
    
    print(f"📦 Stockage (Storage)      : {nb_files} fichiers")
    print("-" * 30)

    # Comparaison
    if nb_logs == nb_files:
        print("✅ PARFAIT ! Tout est synchronisé.")
        print(f"   Il y a exactement {nb_files} fichiers physiques et {nb_logs} preuves juridiques.")
    else:
        print("⚠️ DÉCALAGE DÉTECTÉ.")
        print(f"   Différence : {abs(nb_files - nb_logs)}")
        
        # Afficher les noms pour comprendre
        noms_logs = [l['filename'] for l in response_logs.data]
        noms_files = [f['name'] for f in fichiers_reels]
        
        # Ce qui est dans le Storage mais pas dans les Logs
        for f in noms_files:
            if f not in noms_logs:
                print(f"  ❌ FANTÔME (Dans storage, pas dans logs) : {f}")
                
        # Ce qui est dans les Logs mais pas dans le Storage
        for l in noms_logs:
            if l not in noms_files:
                print(f"  ❌ MANQUANT (Dans logs, pas dans storage) : {l}")

except Exception as e:
    print(f"❌ Erreur critique : {e}")