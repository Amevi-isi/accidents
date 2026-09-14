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

from etl import sanitize_identifier, call_url

# chargement des variables d'environnement
load_dotenv() 
URL_SECURITE = os.getenv("URL_SECURITE")
KOBO_TOKEN = os.getenv("KOBO_TOKEN")
HEADERS = {"Authorization": f"Token {KOBO_TOKEN}"}

# Créer le dossier logs s'il n'existe pas
# Créer le dossier logs dans le dossier parent
parent_dir = os.path.dirname(os.path.abspath(__file__))  # chemin du script
logs_dir = os.path.join(parent_dir, "..", "logs")
os.makedirs(logs_dir, exist_ok=True)

# Numéro de la semaine et année pour le nom du fichier
week_number = datetime.now().strftime("%Y-W%U")  
log_file = os.path.join(logs_dir, f"accidents_{week_number}.log")

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
                contact_parent
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
                %(group_ff3yo15/Parents_contact_s_)s
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
                contact_parent = EXCLUDED.contact_parent
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
                    submission_id_accidents
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
                    %(_id)s
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
                    submission_id_accidents = EXCLUDED.submission_id_accidents
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


def sync_deleted_accidents(conn, current_kobo_ids):
    """
    Supprime tous les accidents absents dans Kobo et leurs dépendances
    (véhicules, passagers, piétons).
    """
    try:
        with conn.cursor() as cur:
            # Récupérer tous les submission_id existants
            cur.execute("SELECT submission_id FROM accidents;")
            db_ids = {row[0] for row in cur.fetchall()}

            # IDs à supprimer
            to_delete = db_ids - set(current_kobo_ids)
            if not to_delete:
                logging.info("Aucun accident supprimé à synchroniser.")
                return

            # Supprimer passagers liés aux véhicules de ces accidents
            cur.execute("""
                DELETE FROM passagers
                WHERE id_vehicules IN (
                    SELECT vehicule_uuid
                    FROM vehicules
                    WHERE submission_id_accidents = ANY(%s)
                );
            """, (list(to_delete),))

            # Supprimer véhicules liés aux accidents
            cur.execute("""
                DELETE FROM vehicules
                WHERE submission_id_accidents = ANY(%s);
            """, (list(to_delete),))

            # Supprimer piétons liés aux accidents
            cur.execute("""
                DELETE FROM pietons
                WHERE submission_id_accidents = ANY(%s);
            """, (list(to_delete),))

            # Supprimer les accidents
            cur.execute("""
                DELETE FROM accidents
                WHERE submission_id = ANY(%s);
            """, (list(to_delete),))

            conn.commit()
            logging.info(f"Accidents et dépendances supprimés : {to_delete}")

    except Exception as e:
        conn.rollback()
        logging.exception(f"Erreur lors de la synchronisation des suppressions : {e}")


def update_database():

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    last_submission = get_last_submission_time(conn) or "2000-11-01T01:02:03"
    datas = fetch_new_submissions(URL_SECURITE, KOBO_TOKEN, last_submission)

    for data in datas:
        id_accident = data["_id"]
        # isertion des information liées à l'accident
        upsert_accidents(conn, data)
        for index, vehicule in enumerate(data["group_th0jz99"]):
            # insertion des info sur les vehicules de l'accident
            vehicule["_id"] = id_accident
            new_id = make_uid(id_accident, index)
            upsert_vehicules(conn, vehicule, new_id)
        
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





if __name__ == "__main__":
   update_database()