-- Total accidents
SELECT COUNT(*) AS total_accidents
FROM public.accidents_view;

-- Accidents par mois
SELECT month, COUNT(*) AS accidents_par_mois
FROM public.accidents_view
GROUP BY month
ORDER BY month;

-- Accidents par région
SELECT region AS region_nom, COUNT(*) AS accidents_par_region
FROM public.accidents_view
GROUP BY region
ORDER BY region;

-- Total véhicules
SELECT COUNT(*) AS total_vehicules
FROM public.vehicules_view;

-- % de véhicules non immatriculés
SELECT
    100.0 * SUM(CASE WHEN TRIM(numero_vehicule) IS NULL OR TRIM(numero_vehicule) = '' THEN 1 ELSE 0 END) / COUNT(*) AS pct_non_immatricules
FROM public.vehicules_view;

-- % de véhicules en mauvais état
SELECT
    100.0 * SUM(CASE WHEN LOWER(etat_avant) = 'mauvais' THEN 1 ELSE 0 END) / COUNT(*) AS pct_mauvais_etat
FROM public.vehicules_view;


-- Total victimes
SELECT COUNT(*) AS total_victimes
FROM public.victimes_view;

-- Victimes par catégorie
SELECT categorie_victime, COUNT(*) AS nb_victimes
FROM public.victimes_view
GROUP BY categorie_victime
ORDER BY categorie_victime;

-- Victimes par type de blessure
SELECT blessures AS type_blessure, COUNT(*) AS nb_victimes
FROM public.victimes_view
GROUP BY blessures
ORDER BY nb_victimes DESC;


-- Taux d'alcool positif
SELECT
    100.0 * SUM(CASE WHEN test_alcool_norm = 'Positif' THEN 1 ELSE 0 END) / COUNT(*) AS taux_alcool_positif
FROM public.victimes_view
WHERE test_alcool_norm IS NOT NULL;

-- Taux de drogue positif
SELECT
    100.0 * SUM(CASE WHEN test_drogue_norm = 'Positif' THEN 1 ELSE 0 END) / COUNT(*) AS taux_drogue_positif
FROM public.victimes_view
WHERE test_drogue_norm IS NOT NULL;

-------------------------------------------------------------------------------
-------- tout dans une table ------------------------------------------

CREATE OR REPLACE VIEW public.superset_metrics_view AS
WITH
-- Accidents
accidents AS (
    SELECT
        COUNT(*) AS total_accidents,
        SUM(CASE WHEN month IS NOT NULL THEN 1 ELSE 0 END) AS accidents_comptes
    FROM public.accidents_view
),
-- Véhicules
vehicules AS (
    SELECT
        COUNT(*) AS total_vehicules,
        100.0 * SUM(CASE WHEN TRIM(numero_vehicule) IS NULL OR TRIM(numero_vehicule) = '' THEN 1 ELSE 0 END) / COUNT(*) AS pct_non_immatricules,
        100.0 * SUM(CASE WHEN LOWER(etat_avant) != 'bon état général' THEN 1 ELSE 0 END) / COUNT(*) AS pct_mauvais_etat
    FROM public.vehicules_view
),
-- Victimes
victimes AS (
    SELECT
        COUNT(*) AS total_victimes,
        SUM(CASE WHEN categorie_victime = 'conducteur' THEN 1 ELSE 0 END) AS nb_conducteurs,
        SUM(CASE WHEN categorie_victime = 'passager' THEN 1 ELSE 0 END) AS nb_passagers,
        SUM(CASE WHEN categorie_victime = 'pieton' THEN 1 ELSE 0 END) AS nb_pietons,
        100.0 * SUM(CASE WHEN test_alcool_norm = 'positif' THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN test_alcool_norm IS NOT NULL THEN 1 ELSE 0 END),0) AS taux_alcool_positif,
        100.0 * SUM(CASE WHEN test_drogue_norm = 'positif' THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN test_drogue_norm IS NOT NULL THEN 1 ELSE 0 END),0) AS taux_drogue_positif
    FROM public.victimes_view
)
SELECT
    a.total_accidents,
    v.total_vehicules,
    v.pct_non_immatricules,
    v.pct_mauvais_etat,
    vi.total_victimes,
    vi.nb_conducteurs,
    vi.nb_passagers,
    vi.nb_pietons,
    vi.taux_alcool_positif,
    vi.taux_drogue_positif
FROM accidents a
CROSS JOIN vehicules v
CROSS JOIN victimes vi;

