CREATE OR REPLACE VIEW public.accidents_view AS
SELECT
    -- Colonnes de base
    submission_id,
    u_uid,
    start_time,
    end_time,
    date_accident,
    heure_accident,
    structure_declarante,
    adresse,
    type_zone,
    type_accident,
    responsabilite,
    poursuite,
    meteo,
    routes,
    type_route,
    submission_time,
    photo_lieu,
    croquis_accident,
    intervention,
    hopital_evacue,
    contact_parent,
    latitude,
    longitude,
    heure_route_degage,
    region,
    prefecture,
    commune,
    canton,

    -- =========================
    -- Colonnes dérivées temporelles
    -- =========================
    EXTRACT(YEAR FROM date_accident)::int            AS year,
    EXTRACT(MONTH FROM date_accident)::int           AS month,
    EXTRACT(DAY FROM date_accident)::int             AS day,
    EXTRACT(HOUR FROM heure_accident)::int           AS hour,
    EXTRACT(DOW FROM date_accident)::int             AS weekday,

    DATE_TRUNC('day', date_accident)::timestamp      AS datetime_trunc_day,
    DATE_TRUNC('month', date_accident)::timestamp    AS datetime_trunc_month,

    -- =========================
    -- Colonnes d’analyse avancée
    -- =========================
    CASE
        WHEN LOWER(type_zone) = 'zone urbaine' THEN TRUE
        ELSE FALSE
    END AS zone_urbaine,

    CASE
        WHEN LOWER(meteo) = 'nuit sans éclairage' THEN TRUE
        ELSE FALSE
    END AS luminosite,

    CASE
        WHEN LOWER(meteo) = 'visibilité réduite par fumée ou poussière' THEN TRUE
        ELSE FALSE
    END AS visibilite

FROM public.accidents;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------

CREATE OR REPLACE VIEW public.vehicules_view AS
SELECT
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
    type_drogue,
    facteurs,
    submission_id_accidents,

    -- Colonne dérivée
    CASE
        WHEN numero_vehicule IS NULL
             OR TRIM(numero_vehicule) = '' THEN FALSE
        ELSE TRUE
    END AS immatricule_bool

FROM public.vehicules;


------------------------------------------------------------------------------------
------------------------------------------------------------------------------------


CREATE OR REPLACE VIEW public.victimes_view AS

-- ============================
-- CONDUCTEURS
-- ============================
SELECT
    v.submission_id_accidents           AS submission_id,
    'conducteur'                        AS categorie_victime,
    v.conducteur_genre                  AS genre_victime,
    v.conducteur_age                    AS age_victime,
    v.conducteur_etat                   AS blessures,
    v.equipement                        AS equipements_victime,
    v.type_vehicule                     AS type_vehicule,
    v.alcool                            AS test_alcool_norm,
    v.drogue                            AS test_drogue_norm
FROM public.vehicules v

UNION ALL

-- ============================
-- PASSAGERS
-- ============================
SELECT
    v.submission_id_accidents           AS submission_id,
    'passager'                          AS categorie_victime,
    p.genre                             AS genre_victime,
    p.age                               AS age_victime,
    p.blessures                         AS blessures,
    p.equipement                        AS equipements_victime,
    v.type_vehicule                     AS type_vehicule,
    NULL                                AS test_alcool_norm,
    NULL                                AS test_drogue_norm
FROM public.passagers p
JOIN public.vehicules v
    ON p.vehicule_uuid_vehicules = v.vehicule_uuid

UNION ALL

-- ============================
-- PIETONS
-- ============================
SELECT
    pi.submission_id_accidents          AS submission_id,
    'pieton'                            AS categorie_victime,
    pi.genre                            AS genre_victime,
    pi.age                              AS age_victime,
    pi.etat                             AS blessures,
    NULL                                AS equipements_victime,
    NULL                                AS type_vehicule,
    NULL                                AS test_alcool_norm,
    NULL                                AS test_drogue_norm
FROM public.pietons pi;


------------------------------------------------------------------------------------
------- jointure des vitimes et des accidents
------------------------------------------------------------------------------------

CREATE OR REPLACE VIEW public.accidents_victimes_full_view AS
SELECT
    a.submission_id               AS submission_id,  -- clé principale
    a.u_uid,
    a.start_time,
    a.end_time,
    a.date_accident,
    a.heure_accident,
    a.structure_declarante,
    a.adresse,
    a.type_zone,
    a.type_accident,
    a.responsabilite,
    a.poursuite,
    a.meteo,
    a.routes,
    a.type_route,
    a.submission_time,
    a.photo_lieu,
    a.croquis_accident,
    a.intervention,
    a.hopital_evacue,
    a.contact_parent,
    a.latitude,
    a.longitude,
    a.heure_route_degage,
    a.region,
    a.prefecture,
    a.commune,
    a.canton,
    a.year,
    a.month,
    a.day,
    a.hour,
    a.weekday,
    a.datetime_trunc_day,
    a.datetime_trunc_month,
    a.zone_urbaine,
    a.luminosite,
    a.visibilite,

    -- Colonnes victimes
    v.categorie_victime,
    v.genre_victime,
    v.age_victime,
    v.blessures,
    v.equipements_victime,
    v.type_vehicule,
    v.test_alcool_norm,
    v.test_drogue_norm

FROM public.accidents_view a
INNER JOIN public.victimes_view v
    ON a.submission_id = v.submission_id;

-----------------------------------------------------------------------------------
-------- 