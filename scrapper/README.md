# Scrapper

> [!NOTE]
> Om de scrapper te runnen moet je `python 3.13` minimaal geïnstalleerd hebben op je machine. Dat moet je doen vanuit `https://www.python.org/downloads/`.

## Uitvoeren van de scrapper

Stap 1: creeër een python virtual environment
```sh
python -m venv venv
```

Stap 2: activeer de virtual enviroment en installeer de packages
```sh
source venv/bin/activate
pip install -r requirements.txt
```

Stap 3: voer de scrapper uit
```sh
python app.py
```

Stap 4: zet de gescrappte data om naar json data.
```sh
python prepare.py
```

> [Back](../README.md)