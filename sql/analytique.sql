-- sumary accident
CREATE VIEW kpi_accidents_summary AS
SELECT
    COUNT(*) AS total_accidents,
    COUNT(DISTINCT submission_id) AS accidents_uniques,
    COUNT(DISTINCT passager_uuid) + COUNT(DISTINCT pieton_uuid) AS total_victimes,
    SUM(CASE WHEN p.age IS NOT NULL AND p.blessures='d_c_s' THEN 1 ELSE 0 END)::float /
        NULLIF(COUNT(DISTINCT passager_uuid) + COUNT(DISTINCT pieton_uuid), 0) AS taux_mortalite
FROM accidents a
LEFT JOIN vehicules v ON v.submission_id_accidents = a.submission_id
LEFT JOIN passagers p ON p.vehicule_uuid_vehicules = v.vehicule_uuid
LEFT JOIN pietons pt ON pt.submission_id_accidents = a.submission_id;


-- Accidents par jour
CREATE VIEW kpi_accidents_daily AS
SELECT 
    DATE_TRUNC('day', date_accident) AS jour,
    COUNT(*) AS nb_accidents
FROM accidents
GROUP BY jour
ORDER BY jour;

-- Accidents par jour de la semaine
CREATE VIEW kpi_accidents_weekday AS
SELECT 
    EXTRACT(DOW FROM date_accident) AS jour_semaine,
    COUNT(*) AS nb_accidents
FROM accidents
GROUP BY jour_semaine
ORDER BY jour_semaine;


-- Répartition par type de véhicules

CREATE VIEW kpi_vehicules_type AS
SELECT 
    type_vehicule,
    COUNT(*) AS nb_vehicules,
    SUM(CASE WHEN numero_vehicule IS NULL THEN 1 ELSE 0 END)::float / COUNT(*) AS pct_non_immatricules,
    SUM(CASE WHEN etat_avant = 'mauvais' THEN 1 ELSE 0 END)::float / COUNT(*) AS pct_mauvais_etat
FROM vehicules
GROUP BY type_vehicule
ORDER BY nb_vehicules DESC;

-- Victimes par gravité

CREATE VIEW kpi_victimes_gravite AS
SELECT 
    etat AS gravite,
    COUNT(*) AS nb_victimes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM (
    SELECT blessures FROM passagers
    UNION ALL
    SELECT etat FROM pietons
) t
GROUP BY etat;

-- Causes et facteurs

CREATE VIEW kpi_alcool_drogue AS
SELECT
    SUM(CASE WHEN alcool='positif' THEN 1 ELSE 0 END)::float / COUNT(*) AS taux_alcool,
    SUM(CASE WHEN drogue='positif' THEN 1 ELSE 0 END)::float / COUNT(*) AS taux_drogue
FROM vehicules v
LEFT JOIN accidents a ON v.submission_id_accidents = a.submission_id;

-- Points noirs et cartographie

CREATE VIEW kpi_points_noirs AS
SELECT 
    ST_Centroid(ST_Collect(geom)) AS centre,
    COUNT(*) AS nb_accidents,
    ARRAY_AGG(submission_id) AS accidents_ids
FROM (
    SELECT ST_SetSRID(ST_MakePoint(geolon, geolat), 4326) AS geom, submission_id
    FROM accidents
) t
GROUP BY ST_ClusterWithin(geom, 50); -- rayon 50 mètres


-- Matrice “Période journalière × Type d'accident”
CREATE OR REPLACE VIEW kpi_matrix_periode_type_accident AS
SELECT
    CASE
        WHEN EXTRACT(HOUR FROM heure_accident) BETWEEN 0 AND 5 THEN 'Nuit'
        WHEN EXTRACT(HOUR FROM heure_accident) BETWEEN 6 AND 11 THEN 'Matin'
        WHEN EXTRACT(HOUR FROM heure_accident) BETWEEN 12 AND 17 THEN 'Après-midi'
        WHEN EXTRACT(HOUR FROM heure_accident) BETWEEN 18 AND 23 THEN 'Soir'
    END AS periode,
    type_accident,
    COUNT(*) AS nb_accidents
FROM accidents
GROUP BY periode, type_accident
ORDER BY periode, type_accident;


-- Répartition des accidents par créneau horaire (00h–23h)
CREATE OR REPLACE VIEW kpi_accidents_hourly AS
SELECT
    EXTRACT(HOUR FROM heure_accident) AS heure,
    COUNT(*) AS nb_accidents
FROM accidents
GROUP BY heure
ORDER BY heure;


-- Répartition des accidents par mois

CREATE OR REPLACE VIEW kpi_accidents_monthly AS
SELECT
    DATE_TRUNC('month', date_accident) AS mois,
    COUNT(*) AS nb_accidents
FROM accidents
GROUP BY mois
ORDER BY mois;

