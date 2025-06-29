import sqlite3
from idlelib.browser import file_open

districts = ["Bemowo","Białołęka","Bielany","Mokotów","Ochota","Praga Południe", "Praga Północ", "Rembertów", "Śródmieście", "Targówek", "Ursus", "Ursynów", "Wawer", "Wesoła", "Wilanów", "Włochy", "Wola", "Żoliborz"]
neighborhoods = {
    "Bemowo": [
        "Bemowo Lotnisko", "Boernerowo", "Chrzanów", "Fort Bema", "Fort Radiowo",
        "Górce", "Groty", "Jelonki Południowe", "Jelonki Północne", "Lotnisko"
    ],
    "Białołęka": [
        "Białołęka Dworska", "Brzeziny", "Choszczówka", "Dąbrówka Szlachecka", "Grodzisk",
        "Henryków", "Kobiałka", "Nowodwory", "Szamocin", "Tarchomin", "Żerań"
    ],
    "Bielany": [
        "Chomiczówka", "Huta", "Las Bielański", "Marymont-Kaskada", "Marymont-Ruda", "Młociny",
        "Piaski", "Placówka", "Radiowo", "Stare Bielany", "Słodowiec", "Wawrzyszew", "Wólka Węglowa", "Wrzeciono"
    ],
    "Mokotów": [
        "Augustówka", "Czerniaków", "Ksawerów", "Sadyba", "Siekierki", "Sielce", "Służew", "Służewiec",
        "Stary Mokotów", "Stegny", "Wierzbno", "Wyględów"
    ],
    "Ochota": [
        "Filtry", "Rakowiec", "Stara Ochota", "Szczęśliwice"
    ],
    "Praga Południe": [
        "Gocław", "Gocławek", "Grochów", "Kamionek", "Olszynka Grochowska", "Saska Kępa"
    ],
    "Praga Północ": [
        "Nowa Praga", "Pelcowizna", "Stara Praga", "Szmulowizna"
    ],
    "Rembertów": [
        "Kawęczyn-Wygoda", "Nowy Rembertów", "Stary Rembertów"
    ],
    "Śródmieście": [
        "Muranów", "Nowe Miasto", "Powiśle", "Solec", "Stare Miasto",
        "Śródmieście Południowe", "Śródmieście Północne", "Ujazdów"
    ],
    "Targówek": [
         "Bródno", "Bródno Podgrodzie", "Elsnerów", "Targówek Fabryczny", "Targówek Mieszkaniowy", "Utrata", "Zacisze"
    ],
    "Ursus": [
        "Czechowice", "Gołąbki", "Niedźwiadek", "Skorosze", "Szamoty"
    ],
    "Ursynów": [
        "Dąbrówka", "Grabów", "Jeziorki Południowe", "Jeziorki Północne", "Kabaty", "Natolin",
        "Pyry", "Skarpa Powsińska", "Stary Imielin", "Stary Służew",
        "Teren Wydzielony Rezerwat „Las Kabacki”", "Ursynów Centrum", "Ursynów Północny", "Wyczółki"
    ],
    "Wawer": [
        "Aleksandrów", "Anin", "Falenica", "Las", "Marysin Wawerski", "Miedzeszyn",
        "Międzylesie", "Nadwiśle", "Radość", "Sadul", "Wawer", "Zerzeń"
    ],
    "Wesoła": [
        "Groszówka", "Plac Wojska Polskiego", "Stara Miłosna", "Wesoła-Centrum", "Wola Grzybowska", "Zielona-Grzybowa"
    ],
    "Wilanów": [
        "Błonia Wilanowskie", "Kępa Zawadowska", "Powsin", "Powsinek",
        "Wilanów Wysoki", "Wilanów Niski", "Wilanów Królewski", "Zawady"
    ],
    "Włochy": [
        "Nowe Włochy", "Okęcie", "Opacz Wielka", "Paluch", "Raków", "Salomea", "Stare Włochy", "Załuski"
    ],
    "Wola": [
        "Czyste", "Koło", "Mirów", "Młynów", "Nowolipki", "Odolany", "Powązki", "Ulrychów"
    ],
    "Żoliborz": [
        "Marymont-Potok", "Sady Żoliborskie", "Stary Żoliborz"
    ]
}

def create_tables():
    con = sqlite3.connect("Streets_clean.db")
    cursor = con.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS districts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        district TEXT UNIQUE NOT NULL
                        )
                        ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS neighborhoods (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        neighborhood TEXT UNIQUE NOT NULL,
                        district_id INTEGER,
                        FOREIGN KEY (district_id) REFERENCES districts(id)
                        )
                        ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS streets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        street TEXT NOT NULL,
                        seen BOOLEAN DEFAULT False
                        )
                        ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS street_neighborhoods (
                        street_id INTEGER,
                        neighborhood_id INTEGER,
                        FOREIGN KEY (street_id) REFERENCES streets(id),
                        FOREIGN KEY (neighborhood_id) REFERENCES neighborhoods(id),
                        PRIMARY KEY (street_id, neighborhood_id)
                        )
                        ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS street_district (
                        street_id INTEGER,
                        district_id INTEGER,
                        FOREIGN KEY (street_id) REFERENCES streets(id),
                        FOREIGN KEY (district_id) REFERENCES districts(id),
                        PRIMARY KEY (street_id, district_id)
                        )
                        ''')
    con.close()

def add_values():
    con = sqlite3.connect("Streets_clean.db")
    cursor = con.cursor()
    for name in districts:
        cursor.execute("INSERT INTO districts (district) VALUES (?)",(name,))
        cursor.execute("SELECT id FROM DISTRICTS WHERE district=?",(name,))
        dist_id = cursor.fetchone()[0]
        neighborhood_list = neighborhoods[name]
        for neigh in neighborhood_list:
            cursor.execute("INSERT INTO neighborhoods (neighborhood,district_id) VALUES (?,?)",(neigh,dist_id))

    con.commit()
    #Adding streets
    with open("streets.txt", "r", encoding="UTF8") as f:
        for line in f:
            info = line.rstrip("\n")
            street,dists,msis = info.split("/")
            district = dists.split(",")
            neighborhood = msis.split(",")
            cursor.execute("INSERT INTO streets (street) VALUES (?)",(street,))
            cursor.execute("SELECT id FROM streets WHERE street = ?",(street,))
            street_id = cursor.fetchone()[0]
            for d in district:
                cursor.execute("SELECT id FROM districts WHERE district = ?",(d,))
                dist = cursor.fetchone()
                if dist:
                    d_id = dist[0]
                    cursor.execute("INSERT INTO street_district (street_id,district_id) VALUES (?,?)",(street_id,d_id))
                else:
                    print(f"District {d} not in database!!!!!\n")
            for n in neighborhood:
                cursor.execute("SELECT id FROM neighborhoods WHERE neighborhood = ?", (n,))
                msi = cursor.fetchone()
                if msi:
                    n_id = msi[0]
                    cursor.execute("INSERT INTO street_neighborhoods (street_id,neighborhood_id) VALUES (?,?)",(street_id,n_id))
                else:
                    print(f"Neighborhood {n} not in database!!!!!\n")
    con.commit()
    con.close()

def create_clean_db():
    create_tables()
    add_values()

if __name__ == '__main__':
    create_clean_db()