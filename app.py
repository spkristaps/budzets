
# Importē nepieciešamās bibliotēkas no Flask un Python
from flask import Flask, render_template, request, redirect, url_for
import csv
import os
from datetime import datetime

# Izveido Flask aplikāciju
app = Flask(__name__)

# Norāda CSV faila nosaukumu, kur glabāsies dati
CSV_FAILS = "dati.csv"

# Saraksts, kurā glabāsies visi ienākumu un izdevumu ieraksti
dati = []


def ieladet_datus():
    """Ielādē datus no CSV faila sarakstā."""
    global dati
    dati = []

    # Pārbauda, vai CSV fails eksistē
    if os.path.exists(CSV_FAILS):
        # Atver failu lasīšanas režīmā
        with open(CSV_FAILS, mode="r", encoding="utf-8", newline="") as fails:
            # Nolasa CSV faila saturu kā vārdnīcas
            lasitajs = csv.DictReader(fails)
            for rinda in lasitajs:
                try:
                    # Pārveido katru rindu par ierakstu ar pareizajiem datu tipiem
                    ieraksts = {
                        "id": int(rinda["id"]),
                        "datums": rinda["datums"],
                        "tips": rinda["tips"],
                        "summa": float(rinda["summa"]),
                        "apraksts": rinda["apraksts"]
                    }
                    # Pievieno ierakstu kopējam datu sarakstam
                    dati.append(ieraksts)
                except (ValueError, KeyError):
                    # Ja kāda rinda ir bojāta vai nepareizi aizpildīta, to izlaiž
                    continue


def saglabat_datus():
    """Saglabā visus datus CSV failā."""
    # Atver CSV failu rakstīšanas režīmā
    with open(CSV_FAILS, mode="w", encoding="utf-8", newline="") as fails:
        # Definē kolonnu nosaukumus
        lauki = ["id", "datums", "tips", "summa", "apraksts"]
        # Izveido rakstītāju CSV failam
        rakstitajs = csv.DictWriter(fails, fieldnames=lauki)
        # Ieraksta galveni
        rakstitajs.writeheader()
        # Ieraksta visus datus failā
        rakstitajs.writerows(dati)


def nakamais_id():
    """Atgriež nākamo unikālo ID."""
    # Ja saraksts ir tukšs, pirmais ID būs 1
    if not dati:
        return 1
    # Atrod lielāko esošo ID un pieskaita 1
    return max(ier["id"] for ier in dati) + 1


def aprekinat_kopsummas(ieraksti):
    """Aprēķina ienākumus, izdevumus un bilanci."""
    # Saskaita visus ienākumus
    ienakumi = sum(ier["summa"] for ier in ieraksti if ier["tips"] == "Ienākums")
    # Saskaita visus izdevumus
    izdevumi = sum(ier["summa"] for ier in ieraksti if ier["tips"] == "Izdevums")
    # Aprēķina bilanci
    bilance = ienakumi - izdevumi
    # Atgriež aprēķinātās vērtības
    return ienakumi, izdevumi, bilance


# Galvenās lapas maršruts
@app.route("/")
def index():
    # Nolasa filtra vērtību no URL parametriem, pēc noklusējuma "Visi"
    filtrs = request.args.get("filtrs", "Visi")
    # Nolasa kļūdas ziņu no URL parametriem, ja tāda ir
    kluda = request.args.get("kluda", "")

    # Filtrē ierakstus pēc izvēlētā tipa
    if filtrs == "Ienākums":
        filtrētie = [ier for ier in dati if ier["tips"] == "Ienākums"]
    elif filtrs == "Izdevums":
        filtrētie = [ier for ier in dati if ier["tips"] == "Izdevums"]
    else:
        filtrētie = dati

    # Aprēķina kopējos ienākumus, izdevumus un bilanci
    ienakumi, izdevumi, bilance = aprekinat_kopsummas(dati)

    # Atver index.html lapu un nodod tai visus vajadzīgos datus
    return render_template(
        "index.html",
        dati=filtrētie,
        filtrs=filtrs,
        kluda=kluda,
        ienakumi=ienakumi,
        izdevumi=izdevumi,
        bilance=bilance
    )


# Maršruts jauna ieraksta pievienošanai
@app.route("/pievienot", methods=["POST"])
def pievienot():
    # Iegūst formas laukus un noņem liekās atstarpes
    tips = request.form.get("tips", "").strip()
    summa_teksts = request.form.get("summa", "").strip()
    apraksts = request.form.get("apraksts", "").strip()
    datums = request.form.get("datums", "").strip()

    # Ja datums nav ievadīts, izmanto šodienas datumu
    if not datums:
        datums = datetime.now().strftime("%Y-%m-%d")

    # Pārbauda, vai tips ir pareizs
    if tips not in ["Ienākums", "Izdevums"]:
        return redirect(url_for("index", kluda="Nepareizs ieraksta tips."))

    # Pārbauda, vai apraksts nav tukšs
    if not apraksts:
        return redirect(url_for("index", kluda="Apraksts nedrīkst būt tukšs."))

    # Pārbauda, vai summa ir korekts skaitlis un lielāka par 0
    try:
        summa = float(summa_teksts)
        if summa <= 0:
            return redirect(url_for("index", kluda="Summai jābūt lielākai par 0."))
    except ValueError:
        return redirect(url_for("index", kluda="Summai jābūt skaitlim."))

    # Izveido jaunu ierakstu
    ieraksts = {
        "id": nakamais_id(),
        "datums": datums,
        "tips": tips,
        "summa": summa,
        "apraksts": apraksts
    }

    # Pievieno ierakstu sarakstam
    dati.append(ieraksts)
    # Saglabā atjaunotos datus CSV failā
    saglabat_datus()

    # Pāradresē atpakaļ uz galveno lapu
    return redirect("/")


# Maršruts ieraksta dzēšanai pēc ID
@app.route("/dzest/<int:ieraksta_id>")
def dzest(ieraksta_id):
    global dati
    # Izveido jaunu sarakstu bez ieraksta ar norādīto ID
    dati = [ier for ier in dati if ier["id"] != ieraksta_id]
    # Saglabā izmaiņas failā
    saglabat_datus()
    # Pāradresē atpakaļ uz galveno lapu
    return redirect("/")


# Maršruts bilances lapai
@app.route("/bilance")
def bilance_lapa():
    # Aprēķina kopējās summas
    ienakumi, izdevumi, bilance = aprekinat_kopsummas(dati)
    # Atver bilance.html lapu un nodod tai aprēķinātās vērtības
    return render_template(
        "bilance.html",
        ienakumi=ienakumi,
        izdevumi=izdevumi,
        bilance=bilance
    )


# Šī daļa tiek izpildīta tikai tad, ja fails tiek palaists tieši
if __name__ == "__main__":
    # Ielādē datus no faila pirms servera palaišanas
    ieladet_datus()
    # Palaiž Flask serveri atkļūdošanas režīmā
    app.run(debug=True)



