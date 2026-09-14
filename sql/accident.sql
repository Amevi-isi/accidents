-- Database generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler version: 0.9.4
-- PostgreSQL version: 13.0
-- Project Site: pgmodeler.io
-- Model Author: ---

-- Database creation must be performed outside a multi lined SQL file. 
-- These commands were put in this file only as a convenience.
-- 
-- object: new_database | type: DATABASE --
-- DROP DATABASE IF EXISTS new_database;
--CREATE DATABASE new_database;
-- ddl-end --


-- object: public.accidents | type: TABLE --
-- DROP TABLE IF EXISTS public.accidents CASCADE;
CREATE TABLE public.accidents (
	submission_id integer NOT NULL,
	u_uid text,
	start_time timestamp,
	end_time timestamp,
	date_accident date,
	heure_accident time,
	structure_declarante text,
	adresse text,
	type_zone text,
	type_accident text,
	responsabilite text,
	poursuite text,
	meteo text,
	routes text,
	type_route text,
	submission_time timestamp,
	photo_lieu text,
	croquis_accident text,
	intervention text,
	hopital_evacue text,
	contact_parent text,
	latitude float8,
	longitude float8,
	heure_route_degage time,
    region text, 
	prefecture text, 
	commune text, 
	canton text,
	CONSTRAINT accidents_pk PRIMARY KEY (submission_id)
);
-- ddl-end --
ALTER TABLE public.accidents OWNER TO mspc;
-- ddl-end --

-- object: public.vehicules | type: TABLE --
-- DROP TABLE IF EXISTS public.vehicules CASCADE;
CREATE TABLE public.vehicules (
	vehicule_uuid text NOT NULL,
	numero_vehicule text,
	type_vehicule text,
	etat_avant text,
	dommages text,
	vitesse text,
	conducteur_genre text,
	conducteur_age text,
	conducteur_etat text,
	equipement text,
	alcool text,
	drogue text,
	type_drogue text,
	facteurs text,
	submission_id_accidents integer,
	CONSTRAINT vehicules_pk PRIMARY KEY (vehicule_uuid)
);
-- ddl-end --
ALTER TABLE public.vehicules OWNER TO mspc;
-- ddl-end --

-- object: public.passagers | type: TABLE --
-- DROP TABLE IF EXISTS public.passagers CASCADE;
CREATE TABLE public.passagers (
	passager_uuid text NOT NULL,
	genre text,
	age text,
	blessures text,
	equipement text,
	vehicule_uuid_vehicules text,
	CONSTRAINT passagers_pk PRIMARY KEY (passager_uuid)
);
-- ddl-end --
ALTER TABLE public.passagers OWNER TO mspc;
-- ddl-end --

-- object: public.pietons | type: TABLE --
-- DROP TABLE IF EXISTS public.pietons CASCADE;
CREATE TABLE public.pietons (
	pieton_uuid text NOT NULL,
	age text,
	etat text,
	genre text,
	submission_id_accidents integer,
	CONSTRAINT pietons_pk PRIMARY KEY (pieton_uuid)
);
-- ddl-end --
ALTER TABLE public.pietons OWNER TO mspc;
-- ddl-end --

-- object: accidents_fk | type: CONSTRAINT --
-- ALTER TABLE public.vehicules DROP CONSTRAINT IF EXISTS accidents_fk CASCADE;
ALTER TABLE public.vehicules ADD CONSTRAINT accidents_fk FOREIGN KEY (submission_id_accidents)
REFERENCES public.accidents (submission_id) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --

-- object: vehicules_fk | type: CONSTRAINT --
-- ALTER TABLE public.passagers DROP CONSTRAINT IF EXISTS vehicules_fk CASCADE;
ALTER TABLE public.passagers ADD CONSTRAINT vehicules_fk FOREIGN KEY (vehicule_uuid_vehicules)
REFERENCES public.vehicules (vehicule_uuid) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --

-- object: accidents_fk | type: CONSTRAINT --
-- ALTER TABLE public.pietons DROP CONSTRAINT IF EXISTS accidents_fk CASCADE;
ALTER TABLE public.pietons ADD CONSTRAINT accidents_fk FOREIGN KEY (submission_id_accidents)
REFERENCES public.accidents (submission_id) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --


