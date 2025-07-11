import sqlite3

class Database:
    def __init__(self,name):
        self.db_name = name
        self.con = sqlite3.connect(self.db_name)
        self.cursor = self.con.cursor()

    def __del__(self):
        self.con.close()

    def how_many_not_seen_in_neighborhood(self,n_id):
        self.cursor.execute("""SELECT COUNT(street) FROM streets
                                    INNER JOIN street_neighborhoods ON streets.id = street_neighborhoods.street_id
                                    WHERE street_neighborhoods.neighborhood_id=? AND seen = 0""", (n_id,))
        value = self.cursor.fetchone()[0]
        return value

    def how_many_not_seen_in_district(self,d_id):
        self.cursor.execute("""SELECT COUNT(street) FROM streets
                                    INNER JOIN street_district ON streets.id = street_district.street_id
                                    WHERE street_district.district_id=? AND seen = 0""", (d_id,))
        value = self.cursor.fetchone()[0]
        return value

    def how_many_not_seen_in_whole_city(self):
        self.cursor.execute("""SELECT COUNT(DISTINCT street) FROM streets WHERE seen = 0""")
        value_all = self.cursor.fetchone()[0]
        return value_all

    def all_streets_in_neighborhood(self,n_id,sort):
        if sort == "name":
            order_by = "streets.id ASC"
        else:
            order_by = "streets.seen DESC,streets.id ASC"
        self.cursor.execute(f"""SELECT streets.id, streets.street, GROUP_CONCAT(DISTINCT districts.district) as all_d,
                                    GROUP_CONCAT(DISTINCT n2.neighborhood) as all_n,
                                    streets.seen FROM streets
                                    JOIN street_neighborhoods sn_filter ON sn_filter.street_id = streets.id
                                    JOIN neighborhoods n_filter ON sn_filter.neighborhood_id = n_filter.id
                                    JOIN street_district ON street_district.street_id = streets.id
                                    JOIN districts ON street_district.district_id = districts.id
                                    JOIN street_neighborhoods sn2 ON sn2.street_id = streets.id
                                    JOIN neighborhoods n2 ON sn2.neighborhood_id = n2.id
                                    WHERE n_filter.id = ?
                                    GROUP BY streets.street
                                    ORDER BY {order_by}""", (n_id,))
        value = self.cursor.fetchall()
        return value

    def all_streets_in_district(self,d_id,sort):
        if sort == "name":
            order_by = "streets.id ASC"
        else:
            order_by = "streets.seen DESC,streets.id ASC"
        self.cursor.execute(f"""SELECT streets.id, streets.street, GROUP_CONCAT(DISTINCT d2.district) as all_d,
                                    GROUP_CONCAT(DISTINCT neighborhoods.neighborhood) as all_n,
                                    streets.seen FROM streets
                                    JOIN street_neighborhoods ON street_neighborhoods.street_id = streets.id
                                    JOIN neighborhoods ON street_neighborhoods.neighborhood_id = neighborhoods.id
                                    JOIN street_district sd_filter ON sd_filter.street_id = streets.id
                                    JOIN districts d_filter ON sd_filter.district_id = d_filter.id
                                    JOIN street_district sd2 ON sd2.street_id = streets.id
                                    JOIN districts d2 ON sd2.district_id = d2.id
                                    WHERE d_filter.id = ?
                                    GROUP BY streets.street
                                    ORDER BY {order_by}""", (d_id,))
        value = self.cursor.fetchall()
        return value

    def search_for_street_name(self,street_name,sort):
        if sort == "name":
            order_by = "streets.id ASC"
        else:
            order_by = "streets.seen DESC,streets.id ASC"
        self.cursor.execute(f"""SELECT streets.id, streets.street, GROUP_CONCAT(DISTINCT districts.district) as all_d,
                                    GROUP_CONCAT(DISTINCT neighborhoods.neighborhood) as all_n,
                                    streets.seen FROM streets
                                    JOIN street_neighborhoods ON street_neighborhoods.street_id = streets.id
                                    JOIN neighborhoods ON street_neighborhoods.neighborhood_id = neighborhoods.id
                                    JOIN street_district ON street_district.street_id = streets.id
                                    JOIN districts ON street_district.district_id = districts.id
                                    WHERE streets.street LIKE ?
                                    GROUP BY streets.street
                                    ORDER BY {order_by}""", (f"%{street_name}%",))
        value = self.cursor.fetchall()
        return value

    def change_seen_value(self,street_id,is_visited):
        if is_visited:
            self.cursor.execute("""UPDATE streets
                                        SET seen = 0
                                        WHERE streets.id = ?""",(street_id,))
        else:
            self.cursor.execute("""UPDATE streets
                                        SET seen = 1
                                        WHERE streets.id = ?""",(street_id,))
        self.con.commit()