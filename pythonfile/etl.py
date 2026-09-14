#!/usr/bin/env python3
import os
import requests
import psycopg2
import psycopg2.extras
import json
from dateutil import parser as dateparser
from typing import Tuple 
from dotenv import load_dotenv
import hashlib
import logging
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point



# Créer le dossier logs s'il n'existe pas
# Créer le dossier logs dans le dossier parent
parent_dir = os.path.dirname(os.path.abspath(__file__))  # chemin du script
logs_dir = os.path.join(parent_dir, "..", "logs")
os.makedirs(logs_dir, exist_ok=True)

# Numéro de la semaine et année pour le nom du fichier
week_number = datetime.now().strftime("%Y-W%U")  
log_file = os.path.join(logs_dir, f"sync_{week_number}.log")

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

##################################################################################
# ------------- CONFIG -------------
# chargement des variables d'environnement
load_dotenv() 
URL_SECURITE = os.getenv("URL_SECURITE")
KOBO_TOKEN = os.getenv("KOBO_TOKEN")
BUNDARIES = os.getenv("BUNDARIES")
HEADERS = {"Authorization": f"Token {KOBO_TOKEN}"}


# ---------- variales Globales -----------
# ------ table accidents -----------

TYPE_ZONE_MAPPING = {
    "zone_urbaine": "zone urbaine",
    "zone_rurale": "zone rurale",
    "p_riph_rie": "périphérie",
    "zone_industrielle": "zone industrielle",
    "zone_r_sidentielle": "zone résidentielle",
}
TYPE_ACCIDENT_MAPPING = {
    "collision_entre_engins_l_gers": "collision entre engins légers",
    "collision_entre_poids_lourds": "collision entre poids lourds",
    "collision_entre_deux_roues": "collision entre deux roues",
    "collision_entre_poids_lourd_et_deux_roue": "collision entre poids lourd et deux roues",
    "collision_entre_engins_l_ger_et_poids_lo": "collision entre engins léger et poids lourd",
    "collision_entre_engins_et_deux_roues": "collision entre engins et deux roues",
    "collision_entre_engins_et_pi_ton": "collision entre engins et piéton",
    "collision_entre_deux_roues_et_pi_ton": "collision entre deux roues et piéton",
    "renversement_de_deux_roues": "renversement de deux roues",
    "sortie_de_route": "sortie de route",
    "choc_avec_obstacle_fixe__mur__poteau__et": "choc avec obstacle fixe (mur, poteau, etc)",
    "choc_avec_obstacle_mobile__animal__etc": "choc avec obstacle mobile (animal, etc)",
    "autre": "autre"
}

RESPONSABILITE_MAPPING = {
    "conducteurs" : "conducteurs",
    "pi_ton": "piéton",
    "tiers": "tiers",
    "inconnue": "inconnue"
}

METEO_MAPPING = {
    "beau_temps": "beau temps",
    "pluie__pendant": "pendant la pluie",
    "pluie__apr_s": "après la pluie",
    "brouillard": "brouillard",
    "vent_fort": "vent fort",
    "chaleur_extr_me": "chaleur extrème",
    "nuit__sans__clairage": "nuit sans éclairage",
    "nuit__avec__clairage": "nuit avec éclairage",
    "visibilit__r_duite_par_fum_e_o": "visibilité réduite par fumée ou poussière",
    "autre": "autre"
}



ROUTE_MAPPING = {
    "route_glissante":	"route glissante",
    "nids_de_poule":	"nids-de-poule",
    "signalisation_absente_ou_inad_":	"signalisation absente ou inadéquate",
    "route_en_bon__tat_g_n_ral":	"route en bon état général",
    "_clairage_insuffisant":	"éclairage insuffisant",
    "obstacle_temporaire_sur_la_rou":	"obstacle temporaire sur la route (débris, animaux, travaux)",
    "route_en_pente_dangereuse":	"route en pente dangereuse",
    "virages_serr_s_ou_mal_signal_s":	"virages serrés ou mal signalés",
    "pr_sence_de_travaux_non_balis_":	"présence de travaux non balisés",
    "route_inond_e_ou_submerg_e":	"route inondée ou submergée",
    "r_tr_cissement_non_signal":	"rétrécissement non signalé",
    "intersection_complexe_ou_mal_o":	"intersection complexe ou mal organisée",
    "absence_de_barri_re_ou_de_prot":	"absence de barrière ou de protection en zones dangereuses",
    "surface_routi_re_in_gale__boss":	"surface routière inégale (bosses, creux)",
    "autre": "autre"
}

TYPE_ROUTE_MAPPING = {
    "autoroute___voie_rapide":	"autoroute / Voie rapide",
    "route_nationale":	"route nationale",
    "route_r_gionale":	"route régionale",
    "route_urbaine":	"route urbaine",
    "rue_r_sidentielle":	"rue résidentielle",
    "chemin_rural_ou_piste_non_am_n":	"chemin rural ou piste non aménagée",
    "rond_point":	"rond-point",
    "pont_echangeur":	"pont/echangeur",
    "voie___sens_unique":	"voie à sens unique",
    "voie___double_sens":	"voie à double sens",
    "route_frontali_re_ou_internati":	"route frontalière ou internationale",
    "autre": "autre"
}

HOPITAL_MAPPING = {
    "clinique_priv_e":	"clinique privée",
    "autre":	"autre",
    "chu":	"CHU",
    "chr":	"CHR",
    "cms":	"CMS",
    "dispensaire":	"dispensaire"
}

# ---- table véhicules ---- 

TYPE_VEHICULE_MAPPING = {
    "voiture_personnelle":	"voiture personnelle",
    "voiture_commerciale":	"voiture commerciale",
    "moto_personnelle":	"moto personnelle",
    "moto_commerciale":	"moto commerciale",
    "poids_lourd_camion":	"poids lourd/camion",
    "bus":	"bus",
    "minibus":	"minibus",
    "v_lo":	"vélo",
    "engin_agricole":	"engin agricole",
    "tricycle__taxi_moto___trois_ro":	"tricycle (taxi-moto à trois roues)",
    "autre__pr_cisez_":	"autre"
}

ETAT_AVANT_MAPPING = {
    "bon__tat_g_n_ral":	"bon état général" ,
    "probl_me_m_canique_connu":"problème mécanique connu" ,
    "pneus_us_s_ou_endommag_s":	"pneus usés ou endommagés", 
    "_quipements_de_s_curit__manqua":	"équipements de sécurité manquants ou défectueux",
    "probl_me_de_freins_signal__ou_":	"problème de freins signalé ou connu",
    "probl_me_de_direction__jeu_ou_":	"problème de direction (jeu ou dysfonctionnement)",
    "_clairage_ou_feux_d_fectueux_o":	"éclairage ou feux défectueux ou inexistants",
    "pare_brise_ou_vitres_endommag_":	"pare-brise ou vitres endommagés ou réduisant la visibilité",
    "surcharg__ou_mal_charg___cas_d":	"surchargé ou mal chargé (cas des engins transportant des biens ou passagers)",
    "r_parations_temporaires_ou_bri":	"réparations temporaires ou bricolées",
    "manque_d_entretien_g_n_ral__vi":	"manque d'entretien général (vidange, contrôle technique, …)",
    "autre__pr_cisez":	"autre"

}

DOMMAGE_MAPPING = {
    "avant":	"avant",
    "arri_re":	"arrière",
    "lat_ral_gauche":	"latéral gauche",
    "lat_ral_droit":	"latéral droit",
    "toit":	"toit",
    "tous_les_c_t_s":	"tous les côtés",
    "aucun_dommage":	"aucun dommage"

}

VITESSE_MAPPING = {
    "_40":	"<=40",
    "40_60":	"41-60",
    "40_60_1":	"61-80",
    "80_100":	"81-100",
    "_100":	"100>",
}


CONDUCTEUR_AGE_MAPPING = {
    "moins_de_18_ans":	"<18",
    "18_30_ans": "18-30",
    "31_50_ans": "31-50",
    "51_65_ans": "51-65",
    "plus_de_65_ans": "65>"

}

ETAT_MAPPING = {
    "aucune":	"aucune",
    "l_g_re":	"légère",
    "grave":	"grave",
    "d_c_s":	"décès"
}

ALCOOL_DROGUE_MAPPING = {
    "non_effectu":	"non effectué",
    "n_gatif":	"négatif",
    "positif":	"positif"

}

FACTEURS_MAPPING = {
    "fatigue":	"fatigue",
    "utilisation_du_t_l_phone_porta":	"utilisation du téléphone portable",
    "exc_s_de_vitesse":	"excès de vitesse",
    "non_respect_des_r_gles_de_prio":	"non-respect des règles de priorité",
    "non_respect_des_feux_de_signal":	"non-respect des feux de signalisation",
    "conduite_sous_influence__alcoo":	"conduite sous influence (alcool/drogue/médicaments)",
    "manque_de_visibilit":	"manque de visibilité",
    "conduite_agressive_ou_impruden":	"conduite agressive ou imprudente",
    "manque_de_formation_ou_d_exp_r":	"manque de formation ou d'expérience",
    "distraction":	"distraction",
    "stress_ou__tat__motionnel_pert":	"stress ou état émotionnel perturbé",
    "non_respect_des_distances_de_s":	"non-respect des distances de sécurité",
    "refus_de_c_der_le_passage___d_":	"refus de céder le passage à d'autres usagers",
    "_tat_de_sant__d_faillant_au_mo":	"etat de santé défaillant au moment de la conduite",
    "transport_d_une_charge_excessi":	"transport d'une charge excessive ou mal arrimée",
    "autre__pr_cisez":	"autre"

}


MAPPINGS = {
    "group_pi79x27/Type_de_zone": TYPE_ZONE_MAPPING,
    "group_pi79x27/Type_d_accident": TYPE_ACCIDENT_MAPPING,
    "Responsabilit_pr_sum_e": RESPONSABILITE_MAPPING,
    "group_yp6ev53/_5_1_Conditions_m_t_orologiques": METEO_MAPPING,
    "group_yp6ev53/_5_2_Conditions_de_la_route": ROUTE_MAPPING,
    "group_yp6ev53/_5_3_Type_de_route": TYPE_ROUTE_MAPPING ,
    "group_ff3yo15/Veuillez_pr_ciser_l_heure_d_ar": HOPITAL_MAPPING,
    "group_th0jz99/_2_2_Type_de_v_hicule": TYPE_VEHICULE_MAPPING,
    "group_th0jz99/_2_3_tat_du_v_hicule_avant_l_a": ETAT_AVANT_MAPPING,
    "group_th0jz99/Dommages_visibles_sur_le_v_hicule": DOMMAGE_MAPPING ,
    "group_th0jz99/Vitesse_estim_e_au_m_l_accident_en_km_h": VITESSE_MAPPING ,
    "group_th0jz99/group_eh8fe47/_ge_approximatif": CONDUCTEUR_AGE_MAPPING,
    "group_th0jz99/group_eh8fe47/Etat_du_conducteur": ETAT_MAPPING,
    "group_th0jz99/group_eh8fe47/_3_4_R_sultat_du_test_d_alcool_": ALCOOL_DROGUE_MAPPING,
    "group_th0jz99/group_eh8fe47/R_sultat_du_test_de_drogue": ALCOOL_DROGUE_MAPPING,
    "group_th0jz99/group_eh8fe47/_3_5_Facteurs_possibles_li_s_au": FACTEURS_MAPPING,
    "group_th0jz99/group_nb8us59/_ge_approximatif_001": CONDUCTEUR_AGE_MAPPING,
    "group_th0jz99/group_nb8us59/Blessures_subies": ETAT_MAPPING,
    "group_nb8us59_001/_ge_approximatif_001_001": CONDUCTEUR_AGE_MAPPING, 
    "group_nb8us59_001/Blessures_subies_001": ETAT_MAPPING
}


# -------- Modification des valeurs par défaut dans la base KOBO ------------

def apply_mapping_recursive(data, mappings):
    if isinstance(data, dict):
        for key, value in data.items():
            try:
                if key in mappings and value is not None:
                    norm = str(value).strip().lower()
                    data[key] = mappings[key].get(norm, value)
                else:
                    data[key] = apply_mapping_recursive(value, mappings)
            except Exception as e:
                logger.error(f"Erreur lors du mapping de la clé '{key}' avec valeur '{value}': {e}")
        return data

    elif isinstance(data, list):
        result = []
        for idx, item in enumerate(data):
            try:
                result.append(apply_mapping_recursive(item, mappings))
            except Exception as e:
                logger.error(f"Erreur lors du mapping de l'élément index {idx}: {e}")
        return result

    # Cas des types simples
    return data

#---- gestion des clés arbitraires -------------
def ensure_key_exists(data: dict, key: str):
    """
    Vérifie si une clé existe dans un dictionnaire.
    Si elle n'existe pas, l'ajoute avec une valeur par défaut.
    """
    try:
        if not isinstance(data, dict):
            logger.error(
                "ensure_key_exists: data n'est pas un dict (type=%s)",
                type(data).__name__
            )
            return data

        if key not in data:
            data[key] = None
            logger.info(
                "Clé absente ajoutée : %s (valeur= None)",
                key
            )

        return data

    except Exception as e:
        logger.error(
            "Erreur lors de l'ajout de la clé '%s' : %s",
            key, e,
            exc_info=True
        )
        return data


# ---------- utilitaires ----------
def parse_datetime(val):
    if not val:
        return None
    try:
        return dateparser.parse(val)
    except Exception:
        return None

def sanitize_identifier(name: str) -> str:
    # from Kobo group names to SQL-friendly suffix, keep letters/numbers/_
    if not name:
        return "unknown"
    s = "".join(c if (c.isalnum() or c == '_') else '_' for c in name).lower()
    # remove repeated underscores
    while '__' in s:
        s = s.replace('__', '_')
    # trim leading/trailing underscores
    return s.strip('_') or 'grp'


# --------- Request on URL ----------

def fetch_json(url, headers, params):
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à {url} : {e}")
        return []
    
def call_url(url: str, headers, params):
    values = fetch_json(url, headers, params)
    return values

# -------- recherche des noms régions et préfectures et communes ---------

def get_admin_names(lat, lon, cantons_gdf):
    """
    Retourne le pays, la région, la préfecture, le canton et la commune
    pour un point donné.
    """
    try:
        # Création du point
        point_gdf = gpd.GeoDataFrame(
            {"latitude": [lat], "longitude": [lon]},
            geometry=[Point(lon, lat)],
            crs="EPSG:4326"
        )

        # Jointure spatiale
        joined = gpd.sjoin(
            point_gdf,
            cantons_gdf,
            how="left",
            predicate="within"
        )

        if joined.empty:
            logger.warning(
                "Aucune subdivision trouvée pour lat=%s, lon=%s", lat, lon
            )
            return {
                "pays": "",
                "region": "",
                "prefecture": "",
                "canton": "",
                "commune": ""
            }

        row = joined.iloc[0]

        return {
            "pays": "Togo",
            "region": row.get("region_nom"),
            "prefecture": row.get("prefectu_1"),
            "commune": row.get("commune_no"),
            "canton": row.get("canton_nom")
        }

    except Exception as e:
        logger.error(
            "Erreur lors de la récupération des subdivisions "
            "(lat=%s, lon=%s) : %s",
            lat, lon, e,
            exc_info=True
        )
        return {
            "pays": "",
            "region": "",
            "prefecture": "",
            "canton": "",
            "commune": ""
        }


# ----- insert and update in tables----

   

def upsert_accidents(conn, row):
    try:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO accidents (
                submission_id, u_uid, start_time, end_time,
                date_accident, heure_accident, structure_declarante, adresse,
                type_zone, type_accident, responsabilite, poursuite,
                meteo, routes, type_route, submission_time,
                photo_lieu, croquis_accident, intervention, hopital_evacue,
                contact_parent, latitude, longitude, heure_route_degage,
                region, prefecture, commune, canton
            )
            VALUES (
                %(_id)s, %(_uuid)s, %(start)s, %(end)s,
                %(group_pi79x27/Date_de_l_accident)s,
                %(group_pi79x27/Heure_de_l_accident)s,
                %(group_pi79x27/Structure_d_clarante)s,
                %(group_pi79x27/Adresse_pr_cise)s,
                %(group_pi79x27/Type_de_zone)s,
                %(group_pi79x27/Type_d_accident)s,
                %(Responsabilit_pr_sum_e)s,
                %(Poursuite_judiciaire)s,
                %(group_yp6ev53/_5_1_Conditions_m_t_orologiques)s,
                %(group_yp6ev53/_5_2_Conditions_de_la_route)s,
                %(group_yp6ev53/_5_3_Type_de_route)s,
                %(_submission_time)s,
                %(group_gb0tk91/_7_1_Photos_des_lieux_disponibl)s,
                %(group_gb0tk91/_7_2_Croquis_de_l_accident_disp)s,
                %(group_ff3yo15/_8_1_Intervention_des_services_)s,
                %(group_ff3yo15/Veuillez_pr_ciser_l_heure_d_ar)s,
                %(group_ff3yo15/Parents_contact_s_)s,
                %(latitude)s, %(longitude)s, %(group_ff3yo15/Route_d_gag_e_)s,
                %(region)s, %(prefecture)s, %(commune)s, %(canton)s
            )
            ON CONFLICT (submission_id) DO UPDATE SET  
                u_uid = EXCLUDED.u_uid,
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time,
                date_accident = EXCLUDED.date_accident,
                heure_accident = EXCLUDED.heure_accident,
                structure_declarante = EXCLUDED.structure_declarante,
                adresse = EXCLUDED.adresse,
                type_zone = EXCLUDED.type_zone,
                type_accident = EXCLUDED.type_accident,
                responsabilite = EXCLUDED.responsabilite,
                poursuite = EXCLUDED.poursuite,
                meteo = EXCLUDED.meteo,
                routes = EXCLUDED.routes,
                type_route = EXCLUDED.type_route,
                submission_time = EXCLUDED.submission_time,
                photo_lieu = EXCLUDED.photo_lieu,
                croquis_accident = EXCLUDED.croquis_accident,
                intervention = EXCLUDED.intervention,
                hopital_evacue = EXCLUDED.hopital_evacue,
                contact_parent = EXCLUDED.contact_parent,
                latitude = EXCLUDED.latitude,       
                longitude = EXCLUDED.longitude,
                heure_route_degage = EXCLUDED.heure_route_degage,
                region = EXCLUDED.region,
                prefecture = EXCLUDED.prefecture, 
                commune = EXCLUDED.commune, 
                canton = EXCLUDED.canton
            RETURNING u_uid;
            """, row)

            uid = cur.fetchone()[0]
            conn.commit()

            logging.info(f"Enregistrement OK - submission_id={row.get('_id')} - u_uid={uid}")
            return uid

    except KeyError as e:
        # Erreur si une clé manque dans row
        conn.rollback()
        logging.error(
            f"Clé manquante dans les données Kobo : {e} - submission_id={row.get('_id')} - row={row}"
        )
    except psycopg2.Error as e:
        # Erreur SQL
        conn.rollback()
        logging.error(
            f"Erreur SQL lors de l'upsert - submission_id={row.get('_id')} - erreur={e.pgerror}"
        )
    except Exception as e:
        # Toute autre erreur
        conn.rollback()
        logging.exception(
            f"Erreur inattendue lors de l'upsert - submission_id={row.get('_id')} - erreur={e}"
        )

    return None

def upsert_vehicules(conn, row, vehicule_uuid):
    """
    Insert / Update un véhicule pour un accident donné.
    row = dictionnaire contenant les champs du formulaire.
    vehicule_uid = identifiant unique stable pour le véhicule
    """

    try:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO vehicules (
                    vehicule_uuid,
                    numero_vehicule,
                    type_vehicule,
                    etat_avant,
                    dommages,
                    vitesse,
                    conducteur_genre,
                    conducteur_age,
                    conducteur_etat,
                    equipement,
                    alcool,
                    drogue,
                    facteurs,
                    submission_id_accidents,
                    type_drogue
                )
                VALUES (
                    %(vehicule_uuid)s,
                    %(group_th0jz99/Num_ro_du_v_hicule)s,
                    %(group_th0jz99/_2_2_Type_de_v_hicule)s,
                    %(group_th0jz99/_2_3_tat_du_v_hicule_avant_l_a)s,
                    %(group_th0jz99/Dommages_visibles_sur_le_v_hicule)s,
                    %(group_th0jz99/Vitesse_estim_e_au_m_l_accident_en_km_h)s,
                    %(group_th0jz99/group_eh8fe47/Genre_du_conducteur)s,
                    %(group_th0jz99/group_eh8fe47/_ge_approximatif)s,
                    %(group_th0jz99/group_eh8fe47/Etat_du_conducteur)s,
                    %(group_th0jz99/group_eh8fe47/Port_d_quipements_de_moment_de_l_accident)s,
                    %(group_th0jz99/group_eh8fe47/_3_4_R_sultat_du_test_d_alcool_)s,
                    %(group_th0jz99/group_eh8fe47/R_sultat_du_test_de_drogue)s,
                    %(group_th0jz99/group_eh8fe47/_3_5_Facteurs_possibles_li_s_au)s,
                    %(_id)s, %(group_th0jz99/group_eh8fe47/Veuillez_pr_ciser_la_drogue)s
                )
                ON CONFLICT (vehicule_uuid) DO UPDATE SET
                    numero_vehicule = EXCLUDED.numero_vehicule,
                    type_vehicule = EXCLUDED.type_vehicule,
                    etat_avant = EXCLUDED.etat_avant,
                    dommages = EXCLUDED.dommages,
                    vitesse = EXCLUDED.vitesse,
                    conducteur_genre = EXCLUDED.conducteur_genre,
                    conducteur_age = EXCLUDED.conducteur_age,
                    conducteur_etat = EXCLUDED.conducteur_etat,
                    equipement = EXCLUDED.equipement,
                    alcool = EXCLUDED.alcool,
                    drogue = EXCLUDED.drogue,
                    facteurs = EXCLUDED.facteurs,
                    submission_id_accidents = EXCLUDED.submission_id_accidents,
                    type_drogue = EXCLUDED.type_drogue
                RETURNING vehicule_uuid;
            """, {**row, "vehicule_uuid": vehicule_uuid})

            inserted_id = cur.fetchone()[0]
            conn.commit()

            logging.info(
                f"Véhicule UPSERT OK - vehicule_uid={vehicule_uuid}"
            )
            return inserted_id

    except KeyError as e:
        conn.rollback()
        logging.error(
            f"Clé manquante dans row pour véhicule : {e} - vehicule_uid={vehicule_uuid} - row={row}"
        )

    except psycopg2.Error as e:
        conn.rollback()
        logging.error(
            f"Erreur SQL lors UPSERT véhicule - vehicule_uid={vehicule_uuid} - erreur={e.pgerror}"
        )

    except Exception as e:
        conn.rollback()
        logging.exception(
            f"Erreur inattendue UPSERT véhicule - vehicule_uid={vehicule_uuid} - erreur={e}"
        )

    return None

def upsert_passagers(conn, row, passager_uuid):
    """
    Insert / Update un passager lié à un véhicule.
    row = dictionnaire contenant les champs du formulaire.
    passager_uuid = identifiant unique stable pour le passager
    """

    try:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO passagers (
                    passager_uuid,
                    genre,
                    age,
                    blessures,
                    equipement,
                    vehicule_uuid_vehicules
                )
                VALUES (
                    %(passager_uuid)s,
                    %(group_th0jz99/group_nb8us59/Genre)s,
                    %(group_th0jz99/group_nb8us59/_ge_approximatif_001)s,
                    %(group_th0jz99/group_nb8us59/Blessures_subies)s,
                    %(group_th0jz99/group_nb8us59/Utilisation_des_qui_rit_le_cas_ch_ant)s,
                    %(_id)s
                )
                ON CONFLICT (passager_uuid) DO UPDATE SET
                    genre = EXCLUDED.genre,
                    age = EXCLUDED.age,
                    blessures = EXCLUDED.blessures,
                    equipement = EXCLUDED.equipement,
                    vehicule_uuid_vehicules = EXCLUDED.vehicule_uuid_vehicules
                RETURNING passager_uuid;
            """, {**row, "passager_uuid": passager_uuid})

            new_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Passager UPSERT OK  passager_uuid={passager_uuid}")

            return new_id

    except KeyError as e:
        conn.rollback()
        logger.error(
            f"Clé manquante dans row pour passager : {e} - passager_uuid={passager_uuid} - row={row}"
        )

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(
            f"Erreur SQL lors UPSERT passager - passager_uuid={passager_uuid} - erreur={e.pgerror}"
        )

    except Exception as e:
        conn.rollback()
        logger.exception(
            f"Erreur inattendue UPSERT passager - passager_uuid={passager_uuid} - erreur={e}"
        )

    return None

def upsert_pietons(conn, row, pieton_uuid):
    """
    Insert / Update un piéton lié à un accident.
    row = dictionnaire contenant les champs du formulaire.
    pieton_uuid = identifiant unique stable pour le piéton
    """

    try:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO pietons (
                    pieton_uuid,
                    age,
                    etat,
                    genre,
                    submission_id_accidents
                )
                VALUES (
                    %(pieton_uuid)s,
                    %(group_nb8us59_001/_ge_approximatif_001_001)s,
                    %(group_nb8us59_001/Blessures_subies_001)s,
                    %(group_nb8us59_001/Genre_001)s,
                    %(_id)s
                )
                ON CONFLICT (pieton_uuid) DO UPDATE SET
                    age = EXCLUDED.age,
                    etat = EXCLUDED.etat,
                    genre = EXCLUDED.genre,
                    submission_id_accidents = EXCLUDED.submission_id_accidents
                RETURNING pieton_uuid;
            """, {**row, "pieton_uuid": pieton_uuid})

            new_uuid = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Piéton UPSERT OK → pieton_uuid={new_uuid}")

            return new_uuid

    except KeyError as e:
        conn.rollback()
        logger.error(
            f"Clé manquante dans row pour piéton : {e} - pieton_uuid={pieton_uuid} - row={row}"
        )

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(
            f"Erreur SQL lors UPSERT piéton - pieton_uuid={pieton_uuid} - erreur={e.pgerror}"
        )

    except Exception as e:
        conn.rollback()
        logger.exception(
            f"Erreur inattendue UPSERT piéton - pieton_uuid={pieton_uuid} - erreur={e}"
        )

    return None

def make_uid(parent_id, index: int) -> str:
    """Génère un UID unique basé sur l'id du parent + index dans la liste."""
    raw = f"{parent_id}_{index}".encode()
    return hashlib.md5(raw).hexdigest()

# ----------- Collecter nouvelles soummissions -----------


def get_last_submission_time(conn) -> str:
    """
    Récupère la dernière date de submission dans la table accidents.
    Retourne None si la table est vide.
    Renvoie la date au format ISO 8601 compatible Kobo: 'YYYY-MM-DDTHH:MM:SS'
    """
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(submission_time) FROM accidents;")
        res = cur.fetchone()
        if res and res[0]:
            # s'assurer que c'est un objet datetime
            if isinstance(res[0], str):
                dt = datetime.fromisoformat(res[0])
            else:
                dt = res[0]
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        return None
    

def fetch_new_submissions(url: str, token: str, last_submission: str) -> list:
    """
    Récupère les nouvelles soumissions depuis l'API Kobo après la date last_submission.
    
    Args:
        url (str): URL de l'API Kobo.
        token (str): Token d'authentification Kobo.
        last_submission (str): Date ISO 8601 de la dernière soumission connue (YYYY-MM-DDTHH:MM:SS).
    
    Returns:
        list: Liste des soumissions (dictionnaires) récupérées.
    """
    params = {
        "format": "json",
        "query": json.dumps({"_submission_time": {"$gt": last_submission}})
    }

    datas = call_url(URL_SECURITE, HEADERS, params)
    
    return datas.get("results", [])

def fetch_all_kobo_ids(url, token):
    headers = {"Authorization": f"Token {token}"}
    params = {"format": "json"}

    data = fetch_json(url, headers, params)
    results = data.get("results", [])

    return [item["_id"] for item in results]


# ------------ Suppression des kobo supprimés -----------

def sync_deleted_accidents(conn, current_kobo_ids):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT submission_id FROM accidents;")
            db_ids = {row[0] for row in cur.fetchall()}

            to_delete = list(db_ids - set(current_kobo_ids))
            if not to_delete:
                return

            cur.execute("""
                DELETE FROM accidents
                WHERE submission_id = ANY(%s);
            """, (to_delete,))

            conn.commit()
            logging.info(f"Accidents supprimés : {to_delete}")

    except Exception:
        conn.rollback()
        logging.exception("Erreur lors de la suppression des accidents")

# ----------- Mise à jour de la base ---------------
def update_database():

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    # recuperer les subdivision administratives
    cantons_gdf = gpd.read_file(BUNDARIES, layer="Cantons")

    last_submission = get_last_submission_time(conn) or "2000-11-01T01:02:03"
    #last_submission = "2000-11-01T01:02:03"
    retrieve_data = fetch_new_submissions(URL_SECURITE, KOBO_TOKEN, last_submission)
    datas = apply_mapping_recursive(retrieve_data, MAPPINGS)
    for data in datas:
        id_accident = data["_id"]
        data["latitude"] = data["_geolocation"][0]
        data["longitude"] = data["_geolocation"][1]
        infos = get_admin_names(data["_geolocation"][0], data["_geolocation"][1], cantons_gdf)
        data["region"], data["prefecture"] = infos["region"], infos["prefecture"]
        data["commune"], data["canton"] =  infos["commune"], infos["canton"]
        # isertion des information liées à l'accident
        upsert_accidents(conn, data)
        for index, vehicule in enumerate(data["group_th0jz99"]):
            # insertion des info sur les vehicules de l'accident
            vehicule["_id"] = id_accident
            new_id = make_uid(id_accident, index)
            vehicule_key = ensure_key_exists(vehicule, "group_th0jz99/group_eh8fe47/Veuillez_pr_ciser_la_drogue")
            upsert_vehicules(conn, vehicule_key, new_id)
        
            for indexp, passager in enumerate(vehicule["group_th0jz99/group_nb8us59"]):
                # insertion des infos sur les passagers du vehicule
                passager["_id"] = new_id
                new_idp = make_uid(new_id, indexp)
                upsert_passagers(conn, passager, new_idp)
        # insertion des piétons impliqués dans l'accident
        for indexpie, pieton in enumerate(data["group_nb8us59_001"]):
            pieton["_id"] = id_accident
            new_idpie = make_uid(id_accident, indexpie)
            upsert_pietons(conn, pieton, new_idpie)

    conn.close()


def synchro_database():

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    ids = fetch_all_kobo_ids(URL_SECURITE, KOBO_TOKEN)
    sync_deleted_accidents(conn, ids)
    
    conn.close()


if __name__ == "__main__":
    update_database()
    synchro_database()