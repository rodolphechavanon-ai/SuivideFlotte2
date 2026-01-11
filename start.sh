#!/bin/bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

5. Clique sur **"Commit new file"**

✅ **Fichier créé !**

---

## **ÉTAPE 3 : Déployer sur Render**

### **Sur Render.com** :

1. **Connecte ton GitHub** :
   - Clique sur ton profil (en haut à droite)
   - **"Account Settings"** → **"Connect GitHub"**
   - Autorise Render à accéder à tes repositories

2. **Créer le Web Service** :
   - Reviens au Dashboard Render
   - Clique sur **"New +"** (en haut à droite)
   - Sélectionne **"Web Service"**

3. **Sélectionne ton repository** :
   - Cherche `suivideflotte2` (ou le nom de ton repo)
   - Clique sur **"Connect"**

4. **Configure le service** :
```
   Name: suivideflotte-intelligence
   Region: Frankfurt (ou le plus proche)
   Branch: main
   Root Directory: (laisse vide)
   Runtime: Python 3
   
   Build Command:
   pip install -r requirements.txt
   
   Start Command:
   bash start.sh
