from flask import Flask, render_template, request, redirect, url_for
import csv
import os
from datetime import datetime

app = Flask(__name__)

CSV_FAILS = "dati.csv"
dati = []


def ieladet_datus():
    """Ielādē datus no CSV faila sarakstā."""
    global dati
    dati = []

    if os.path.exists(CSV_FAILS):
        with open(CSV_FAILS, mode="r", encoding="utf-8", newline="") as fails:
            lasitajs = csv.DictReader(fails)
            for rinda in lasitajs:
                try:
                    ieraksts = {
                        "id": int(rinda["id"]),
                        "datums": rinda["datums"],
                        "tips": rinda["tips"],
                        "summa": float(rinda["summa"]),
                        "apraksts": rinda["apraksts"]
                    }
                    dati.append(ieraksts)
                except (ValueError, KeyError):
                    # Ja kāda rinda bojāta, to izlaiž
                    continue


def saglabat_datus():
    """Saglabā visus datus CSV failā."""
    with open(CSV_FAILS, mode="w", encoding="utf-8", newline="") as fails:
        lauki = ["id", "datums", "tips", "summa", "apraksts"]
        rakstitajs = csv.DictWriter(fails, fieldnames=lauki)
        rakstitajs.writeheader()
        rakstitajs.writerows(dati)


def nakamais_id():
    """Atgriež nākamo unikālo ID."""
    if not dati:
        return 1
    return max(ier["id"] for ier in dati) + 1


def aprekinat_kopsummas(ieraksti):
    """Aprēķina ienākumus, izdevumus un bilanci."""
    ienakumi = sum(ier["summa"] for ier in ieraksti if ier["tips"] == "Ienākums")
    izdevumi = sum(ier["summa"] for ier in ieraksti if ier["tips"] == "Izdevums")
    bilance = ienakumi - izdevumi
    return ienakumi, izdevumi, bilance


@app.route("/")
def index():
    filtrs = request.args.get("filtrs", "Visi")
    kluda = request.args.get("kluda", "")

    if filtrs == "Ienākums":
        filtrētie = [ier for ier in dati if ier["tips"] == "Ienākums"]
    elif filtrs == "Izdevums":
        filtrētie = [ier for ier in dati if ier["tips"] == "Izdevums"]
    else:
        filtrētie = dati

    ienakumi, izdevumi, bilance = aprekinat_kopsummas(dati)

    return render_template(
        "index.html",
        dati=filtrētie,
        filtrs=filtrs,
        kluda=kluda,
        ienakumi=ienakumi,
        izdevumi=izdevumi,
        bilance=bilance
    )


@app.route("/pievienot", methods=["POST"])
def pievienot():
    tips = request.form.get("tips", "").strip()
    summa_teksts = request.form.get("summa", "").strip()
    apraksts = request.form.get("apraksts", "").strip()
    datums = request.form.get("datums", "").strip()

    if not datums:
        datums = datetime.now().strftime("%Y-%m-%d")

    if tips not in ["Ienākums", "Izdevums"]:
        return redirect(url_for("index", kluda="Nepareizs ieraksta tips."))

    if not apraksts:
        return redirect(url_for("index", kluda="Apraksts nedrīkst būt tukšs."))

    try:
        summa = float(summa_teksts)
        if summa <= 0:
            return redirect(url_for("index", kluda="Summai jābūt lielākai par 0."))
    except ValueError:
        return redirect(url_for("index", kluda="Summai jābūt skaitlim."))

    ieraksts = {
        "id": nakamais_id(),
        "datums": datums,
        "tips": tips,
        "summa": summa,
        "apraksts": apraksts
    }

    dati.append(ieraksts)
    saglabat_datus()

    return redirect("/")


@app.route("/dzest/<int:ieraksta_id>")
def dzest(ieraksta_id):
    global dati
    dati = [ier for ier in dati if ier["id"] != ieraksta_id]
    saglabat_datus()
    return redirect("/")


@app.route("/bilance")
def bilance_lapa():
    ienakumi, izdevumi, bilance = aprekinat_kopsummas(dati)
    return render_template(
        "bilance.html",
        ienakumi=ienakumi,
        izdevumi=izdevumi,
        bilance=bilance
    )


if __name__ == "__main__":
    ieladet_datus()
    app.run(debug=True)



