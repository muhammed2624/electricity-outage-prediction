"""
street_grid_registry seed data -- NATIONWIDE (all 11 DisCo territories).

WHY THIS EXISTS: no public dataset maps individual Nigerian streets to
their DisCo/feeder/service-band. This seed table demonstrates the real
architecture Voltix would use in production, populated with genuinely
correct DisCo assignments for well-known areas in each DisCo's core
service city.

WHAT'S VERIFIED vs ESTIMATED:
  - area_neighborhood, lga, state, disco_id  -> the AREA and its DisCo are
    real, well-documented facts (each DisCo's franchise territory is
    public regulatory information, e.g. AEDC serves the FCT including
    Abuja city, KEDCO serves Kano, PHED serves Port Harcourt/Rivers,
    etc.). Confirmed against each DisCo's publicly stated coverage area.
  - feeder_code, service_band                -> NOT independently
    verified (no public feeder-level registry exists for any DisCo).
    Marked 'estimated' in the confidence column and should be replaced
    with real DisCo/NERC feeder records before any production use.

This keeps the product honest: users searching a real area get a real
DisCo, but are told plainly when the feeder/band shown is an estimate.

COVERAGE NOTE: this is a seed table, not an exhaustive national gazetteer.
It gives every one of the 11 DisCos in master_discos_monthly.csv genuine
area-level entries in their real core city/cities, so the app is no
longer Lagos-only -- but it is still a representative sample (6-17
areas per DisCo), not a street-by-street census of Nigeria. That
limitation is stated in the app's methodology panel.
"""

import csv
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "street_grid_registry.csv"

# (street_name, area_neighborhood, lga, state, disco_id, feeder_code_estimate, service_band_estimate, confidence)
# disco_id values match the DisCo names used in master_discos_monthly.csv
# ("Ikeja", "Eko", "Abuja", "Benin", "Enugu", "Ibadan", "Jos", "Kaduna",
# "Kano", "Port Harcourt", "Yola") so predictions flow straight from
# area -> disco -> the existing trained nationwide model.
ROWS = [
    # ---------------------------------------------------------------
    # Ikeja Electric territory (mainland / northern Lagos)
    # ---------------------------------------------------------------
    ("Obafemi Awolowo Way", "Ikeja GRA", "Ikeja", "Lagos", "Ikeja", "IKJ-GRA-F1", "A", "estimated"),
    ("Allen Avenue", "Ikeja", "Ikeja", "Lagos", "Ikeja", "IKJ-ALN-F2", "A", "estimated"),
    ("Opebi Road", "Opebi", "Ikeja", "Lagos", "Ikeja", "IKJ-OPB-F1", "A", "estimated"),
    ("Adeniyi Jones Avenue", "Ikeja", "Ikeja", "Lagos", "Ikeja", "IKJ-ADJ-F3", "B", "estimated"),
    ("Toyin Street", "Ikeja", "Ikeja", "Lagos", "Ikeja", "IKJ-TYN-F1", "B", "estimated"),
    ("Herbert Macaulay Way", "Yaba", "Lagos Mainland", "Lagos", "Ikeja", "YAB-HBM-F1", "B", "estimated"),
    ("Commercial Avenue", "Yaba", "Lagos Mainland", "Lagos", "Ikeja", "YAB-CML-F2", "B", "estimated"),
    ("Adeniran Ogunsanya Street", "Surulere", "Surulere", "Lagos", "Ikeja", "SUR-ADO-F1", "B", "estimated"),
    ("Bode Thomas Street", "Surulere", "Surulere", "Lagos", "Ikeja", "SUR-BDT-F2", "B", "estimated"),
    ("Agege Motor Road", "Mushin", "Mushin", "Lagos", "Ikeja", "MSH-AGM-F1", "C", "estimated"),
    ("Oshodi-Apapa Expressway", "Oshodi", "Oshodi-Isolo", "Lagos", "Ikeja", "OSH-EXP-F1", "C", "estimated"),
    ("Ikorodu Road", "Ketu", "Kosofe", "Lagos", "Ikeja", "KET-IKR-F1", "B", "estimated"),
    ("CMD Road", "Magodo", "Kosofe", "Lagos", "Ikeja", "MGD-CMD-F1", "A", "estimated"),
    ("Sangotedo Road", "Ikorodu", "Ikorodu", "Lagos", "Ikeja", "IKR-SGT-F1", "C", "estimated"),
    ("Abule Egba Expressway", "Abule Egba", "Ifako-Ijaiye", "Lagos", "Ikeja", "ABE-EXP-F1", "C", "estimated"),
    ("Akowonjo Road", "Akowonjo", "Alimosho", "Lagos", "Ikeja", "AKW-RD-F1", "C", "estimated"),
    ("Egbeda Idimu Road", "Egbeda", "Alimosho", "Lagos", "Ikeja", "EGB-IDM-F1", "C", "estimated"),

    # ---------------------------------------------------------------
    # Eko DisCo territory (island / southern Lagos) -- per EKEDC's own
    # published 12 districts: Lekki, Ibeju, Islands, Ajah, Ajele, Orile,
    # Ijora, Apapa, Mushin[part], Festac, Ojo, Agbara
    # ---------------------------------------------------------------
    ("Adetokunbo Ademola Street", "Victoria Island", "Eti-Osa", "Lagos", "Eko", "VI-ADT-F1", "A", "estimated"),
    ("Ahmadu Bello Way", "Victoria Island", "Eti-Osa", "Lagos", "Eko", "VI-AHB-F2", "A", "estimated"),
    ("Bourdillon Road", "Ikoyi", "Eti-Osa", "Lagos", "Eko", "IKY-BRD-F1", "A", "estimated"),
    ("Awolowo Road", "Ikoyi", "Eti-Osa", "Lagos", "Eko", "IKY-AWL-F2", "A", "estimated"),
    ("Admiralty Way", "Lekki Phase 1", "Eti-Osa", "Lagos", "Eko", "LKI-ADM-F1", "A", "estimated"),
    ("Freedom Way", "Lekki Phase 1", "Eti-Osa", "Lagos", "Eko", "LKI-FDM-F2", "B", "estimated"),
    ("Ajah-Sangotedo Road", "Ajah", "Eti-Osa", "Lagos", "Eko", "AJH-RD-F1", "C", "estimated"),
    ("Marina Street", "Lagos Island", "Lagos Island", "Lagos", "Eko", "LGI-MRN-F1", "A", "estimated"),
    ("Broad Street", "Lagos Island", "Lagos Island", "Lagos", "Eko", "LGI-BRD-F2", "A", "estimated"),
    ("Wharf Road", "Apapa", "Apapa", "Lagos", "Eko", "APP-WRF-F1", "B", "estimated"),
    ("Creek Road", "Apapa", "Apapa", "Lagos", "Eko", "APP-CRK-F2", "B", "estimated"),
    ("22 Road", "Festac Town", "Amuwo-Odofin", "Lagos", "Eko", "FST-22R-F1", "C", "estimated"),
    ("First Avenue", "Festac Town", "Amuwo-Odofin", "Lagos", "Eko", "FST-1AV-F2", "C", "estimated"),
    ("Trade Fair Road", "Ojo", "Ojo", "Lagos", "Eko", "OJO-TFR-F1", "D", "estimated"),
    ("Agbara Estate Road", "Agbara", "Agbara-Igbesa", "Ogun", "Eko", "AGB-EST-F1", "C", "estimated"),

    # ---------------------------------------------------------------
    # Abuja Electricity Distribution Company (AEDC) -- FCT / Abuja city
    # ---------------------------------------------------------------
    ("Aminu Kano Crescent", "Wuse 2", "Municipal Area Council", "FCT", "Abuja", "WU2-AMK-F1", "A", "estimated"),
    ("Ademola Adetokunbo Crescent", "Wuse 2", "Municipal Area Council", "FCT", "Abuja", "WU2-ADT-F2", "A", "estimated"),
    ("Constitution Avenue", "Central Business District", "Municipal Area Council", "FCT", "Abuja", "CBD-CST-F1", "A", "estimated"),
    ("Tafawa Balewa Way", "Area 3, Garki", "Municipal Area Council", "FCT", "Abuja", "GRK-TFB-F1", "B", "estimated"),
    ("Ahmadu Bello Way", "Garki", "Municipal Area Council", "FCT", "Abuja", "GRK-AHB-F2", "A", "estimated"),
    ("Yakubu Gowon Crescent", "Asokoro", "Municipal Area Council", "FCT", "Abuja", "ASK-YKG-F1", "A", "estimated"),
    ("Aso Drive", "Asokoro", "Municipal Area Council", "FCT", "Abuja", "ASK-ASD-F2", "A", "estimated"),
    ("Gana Street", "Maitama", "Municipal Area Council", "FCT", "Abuja", "MTM-GNA-F1", "A", "estimated"),
    ("Panama Street", "Maitama", "Municipal Area Council", "FCT", "Abuja", "MTM-PNM-F2", "A", "estimated"),
    ("1st Avenue", "Gwarinpa", "Municipal Area Council", "FCT", "Abuja", "GWP-1AV-F1", "B", "estimated"),
    ("Kubwa Expressway", "Kubwa", "Bwari Area Council", "FCT", "Abuja", "KBW-EXP-F1", "C", "estimated"),
    ("Nyanya-Karu Road", "Nyanya", "Municipal Area Council", "FCT", "Abuja", "NYN-RD-F1", "C", "estimated"),
    ("Lugbe Airport Road", "Lugbe", "Municipal Area Council", "FCT", "Abuja", "LGB-APT-F1", "C", "estimated"),

    # ---------------------------------------------------------------
    # Benin Electricity Distribution Company (BEDC) -- Benin City, Edo
    # ---------------------------------------------------------------
    ("Sapele Road", "Benin City", "Oredo", "Edo", "Benin", "BNC-SPL-F1", "B", "estimated"),
    ("Airport Road", "Benin City", "Oredo", "Edo", "Benin", "BNC-APT-F1", "B", "estimated"),
    ("Ring Road", "Benin City", "Oredo", "Edo", "Benin", "BNC-RNG-F1", "A", "estimated"),
    ("Akpakpava Street", "Benin City", "Oredo", "Edo", "Benin", "BNC-AKP-F1", "B", "estimated"),
    ("Mission Road", "Benin City", "Oredo", "Edo", "Benin", "BNC-MSN-F1", "B", "estimated"),
    ("Reservation Road", "GRA", "Oredo", "Edo", "Benin", "BNC-GRA-F1", "A", "estimated"),
    ("Lagos Road", "Ugbowo", "Ovia North-East", "Edo", "Benin", "UGB-LAG-F1", "C", "estimated"),
    ("Sokponba Road", "Benin City", "Oredo", "Edo", "Benin", "BNC-SKP-F1", "C", "estimated"),
    ("New Benin Market Road", "New Benin", "Oredo", "Edo", "Benin", "NBN-MKT-F1", "C", "estimated"),
    ("Ekenwan Road", "Benin City", "Oredo", "Edo", "Benin", "BNC-EKN-F1", "B", "estimated"),
    ("Uselu-Lagos Road", "Uselu", "Egor", "Edo", "Benin", "USL-LAG-F1", "C", "estimated"),

    # ---------------------------------------------------------------
    # Enugu Electricity Distribution Company (EEDC) -- Enugu city
    # ---------------------------------------------------------------
    ("Presidential Road", "Independence Layout", "Enugu North", "Enugu", "Enugu", "IND-PRS-F1", "A", "estimated"),
    ("Ebeano Street", "Achara Layout", "Enugu South", "Enugu", "Enugu", "ACH-EBN-F1", "B", "estimated"),
    ("Chime Avenue", "New Haven", "Enugu North", "Enugu", "Enugu", "NHV-CHM-F1", "A", "estimated"),
    ("Ogui Road", "Ogui", "Enugu North", "Enugu", "Enugu", "OGI-RD-F1", "B", "estimated"),
    ("Zik Avenue", "Uwani", "Enugu South", "Enugu", "Enugu", "UWN-ZIK-F1", "B", "estimated"),
    ("Abakaliki Road", "Enugu", "Enugu North", "Enugu", "Enugu", "ENU-ABK-F1", "C", "estimated"),
    ("Agbani Road", "Enugu", "Enugu South", "Enugu", "Enugu", "ENU-AGB-F1", "C", "estimated"),
    ("Okpara Avenue", "Enugu", "Enugu North", "Enugu", "Enugu", "ENU-OKP-F1", "A", "estimated"),
    ("Abakpa Road", "Trans-Ekulu", "Enugu East", "Enugu", "Enugu", "TEK-ABK-F1", "C", "estimated"),

    # ---------------------------------------------------------------
    # Ibadan Electricity Distribution Company (IBEDC) -- Ibadan, Oyo
    # ---------------------------------------------------------------
    ("Ring Road", "Ring Road", "Ibadan South-West", "Oyo", "Ibadan", "IBD-RNG-F1", "B", "estimated"),
    ("Awolowo Road", "Bodija", "Ibadan North", "Oyo", "Ibadan", "BDJ-AWL-F1", "A", "estimated"),
    ("Lebanon Street", "Dugbe", "Ibadan South-West", "Oyo", "Ibadan", "DGB-LBN-F1", "B", "estimated"),
    ("Ogunpa Street", "Ogunpa", "Ibadan North-East", "Oyo", "Ibadan", "OGP-RD-F1", "C", "estimated"),
    ("Iwo Road", "Iwo Road", "Ibadan North-East", "Oyo", "Ibadan", "IWR-RD-F1", "C", "estimated"),
    ("Sango-UI Road", "Sango", "Ibadan North", "Oyo", "Ibadan", "SNG-UI-F1", "B", "estimated"),
    ("Mokola Road", "Mokola", "Ibadan North", "Oyo", "Ibadan", "MKL-RD-F1", "B", "estimated"),
    ("Challenge Road", "Challenge", "Ibadan South-West", "Oyo", "Ibadan", "CHL-RD-F1", "C", "estimated"),
    ("Molete Road", "Molete", "Ibadan South-West", "Oyo", "Ibadan", "MLT-RD-F1", "C", "estimated"),
    ("University Road", "Agbowo", "Ibadan North", "Oyo", "Ibadan", "AGB-UNI-F1", "B", "estimated"),

    # ---------------------------------------------------------------
    # Jos Electricity Distribution Company (JED) -- Jos, Plateau
    # ---------------------------------------------------------------
    ("Rayfield Road", "Rayfield", "Jos South", "Plateau", "Jos", "RYF-RD-F1", "A", "estimated"),
    ("Bukuru Bye-Pass", "Bukuru", "Jos South", "Plateau", "Jos", "BKR-BYP-F1", "C", "estimated"),
    ("Ahmadu Bello Way", "Terminus", "Jos North", "Plateau", "Jos", "TRM-AHB-F1", "B", "estimated"),
    ("Yakubu Gowon Way", "Jos", "Jos North", "Plateau", "Jos", "JOS-YKG-F1", "B", "estimated"),
    ("Bauchi Road", "Farin Gada", "Jos North", "Plateau", "Jos", "FRG-BCH-F1", "C", "estimated"),
    ("Old Airport Road", "Jos", "Jos North", "Plateau", "Jos", "JOS-OAP-F1", "B", "estimated"),

    # ---------------------------------------------------------------
    # Kaduna Electric (KAEDCO) -- Kaduna city
    # ---------------------------------------------------------------
    ("Constitution Road", "Barnawa", "Kaduna South", "Kaduna", "Kaduna", "BRN-CST-F1", "B", "estimated"),
    ("Sabon Gari Road", "Sabon Gari", "Kaduna North", "Kaduna", "Kaduna", "SGK-RD-F1", "C", "estimated"),
    ("Malali Road", "Malali", "Kaduna North", "Kaduna", "Kaduna", "MLL-RD-F1", "B", "estimated"),
    ("Isa Kaita Road", "Ungwan Rimi", "Kaduna North", "Kaduna", "Kaduna", "UGR-ISK-F1", "A", "estimated"),
    ("Ali Akilu Road", "Tudun Wada", "Kaduna South", "Kaduna", "Kaduna", "TDW-ALK-F1", "B", "estimated"),
    ("Ahmadu Bello Way", "Kaduna", "Kaduna North", "Kaduna", "Kaduna", "KAD-AHB-F1", "A", "estimated"),

    # ---------------------------------------------------------------
    # Kano Electricity Distribution Company (KEDCO) -- Kano city
    # ---------------------------------------------------------------
    ("Ibrahim Taiwo Road", "Sabon Gari", "Kano Municipal", "Kano", "Kano", "SGK-IBT-F1", "B", "estimated"),
    ("Zoo Road", "Zoo Road", "Nassarawa", "Kano", "Kano", "ZOO-RD-F1", "B", "estimated"),
    ("Bompai Road", "Bompai", "Nassarawa", "Kano", "Kano", "BMP-RD-F1", "A", "estimated"),
    ("Airport Road", "Kano", "Nassarawa", "Kano", "Kano", "KAN-APT-F1", "A", "estimated"),
    ("Murtala Mohammed Way", "Fagge", "Fagge", "Kano", "Kano", "FGG-MRM-F1", "C", "estimated"),
    ("Sharada Road", "Sharada", "Kano Municipal", "Kano", "Kano", "SHR-RD-F1", "C", "estimated"),

    # ---------------------------------------------------------------
    # Port Harcourt Electricity Distribution Company (PHED) -- Rivers
    # ---------------------------------------------------------------
    ("GRA Phase 2 Road", "GRA Phase 2", "Port Harcourt City", "Rivers", "Port Harcourt", "GRA2-RD-F1", "A", "estimated"),
    ("Trans Amadi Industrial Layout", "Trans Amadi", "Port Harcourt City", "Rivers", "Port Harcourt", "TRA-IND-F1", "B", "estimated"),
    ("Aba Road", "Port Harcourt", "Port Harcourt City", "Rivers", "Port Harcourt", "PHC-ABA-F1", "B", "estimated"),
    ("Rumuola Road", "Rumuola", "Obio-Akpor", "Rivers", "Port Harcourt", "RML-RD-F1", "B", "estimated"),
    ("Woji Road", "Woji", "Obio-Akpor", "Rivers", "Port Harcourt", "WOJ-RD-F1", "C", "estimated"),
    ("Ada George Road", "Elelenwo", "Obio-Akpor", "Rivers", "Port Harcourt", "ELN-ADG-F1", "C", "estimated"),

    # ---------------------------------------------------------------
    # Yola Electricity Distribution Company (YEDC) -- Yola, Adamawa
    # ---------------------------------------------------------------
    ("Bekaji Road", "Jimeta", "Yola North", "Adamawa", "Yola", "JMT-BKJ-F1", "B", "estimated"),
    ("Galadima Aminu Way", "Jimeta", "Yola North", "Adamawa", "Yola", "JMT-GLD-F1", "A", "estimated"),
    ("Bank Road", "Rock Haven", "Yola South", "Adamawa", "Yola", "RCH-BNK-F1", "B", "estimated"),
    ("Numan Road", "Karewa", "Yola North", "Adamawa", "Yola", "KRW-NMN-F1", "C", "estimated"),
    ("Atiku Abubakar Way", "Nasarawo", "Yola South", "Adamawa", "Yola", "NSR-ATB-F1", "B", "estimated"),
]

HEADER = ["street_name", "area_neighborhood", "lga", "state", "disco_id", "feeder_code", "service_band", "confidence"]

if __name__ == "__main__":
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(ROWS)
    print(f"Wrote {len(ROWS)} rows to {OUT_PATH}")

    # Quick sanity check: every disco_id in the registry should exist in
    # the trained model's DisCo list, or the app will silently break for
    # that area. Run this after every edit to ROWS.
    import pandas as pd
    master_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "master_discos_monthly.csv"
    if master_path.exists():
        model_discos = set(pd.read_csv(master_path)["DisCo"].unique())
        registry_discos = {r[4] for r in ROWS}
        missing = registry_discos - model_discos
        if missing:
            print(f"WARNING: these disco_id values are not in master_discos_monthly.csv: {missing}")
        else:
            print(f"OK: all {len(registry_discos)} disco_id values match the trained model's DisCo list.")
        uncovered = model_discos - registry_discos
        if uncovered:
            print(f"NOTE: these DisCos have no registry entries yet: {uncovered}")
