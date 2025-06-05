from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
app.secret_key = 'cle_secrete'

VALID_USERNAME = 'client'
VALID_PASSWORD = '1234'

# Charger le fichier Excel une fois au démarrage
try:
    df_tarifs = pd.read_excel('Tarifs_ludagri.xlsx')
    print("Excel chargé, colonnes :", df_tarifs.columns.tolist())
except Exception as e:
    print("Erreur chargement Excel :", e)
    df_tarifs = pd.DataFrame()

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == VALID_USERNAME and request.form['password'] == VALID_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('search'))
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    reference = None
    designation = None
    price = None
    message = None

    if request.method == 'POST':
        reference = request.form['reference'].strip()
        print(f"Recherche pour la référence : {reference}")

        # Chercher dans Excel
        if not df_tarifs.empty:
            found = df_tarifs[df_tarifs['Reference'].astype(str).str.strip() == reference]
            if not found.empty:
                designation = found.iloc[0]['Designation']
                price = found.iloc[0]['Prix']
                print(f"Trouvé dans Excel : {designation} à {price} €")
            else:
                try:
                    url = f"https://www.avkparts.lt/search/{reference}"
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    texts = [el.get_text(strip=True) for el in soup.find_all(text=True)]
                    print(f"Nombre total de textes extraits: {len(texts)}")
                    for i, t in enumerate(texts):
                        print(f"{i}: {t}")
                    
                    # Recherche du premier prix HT au format euro
                    prix_ht = None
                    for t in texts:
                        match = re.search(r"\u20ac\s?(\d+[\.,]\d{2})", t)
                        if match:
                            prix_ht = float(match.group(1).replace(',', '.'))
                            break
                    
                    if prix_ht:
                        designation = reference
                        price = round(prix_ht * 1.5, 2)
                    else:
                        message = "Aucun prix HT trouvé sur AVK"
                        print(message)

                except Exception as e:
                    message = "Prix indisponible pour cette référence"
                    print(message)
        else:
            message = "Fichier Excel non chargé."
            print(message)

    return render_template('search.html', reference=reference, designation=designation, price=price, message=message)

if __name__ == '__main__':
    app.run(debug=True)