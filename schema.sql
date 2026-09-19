--
-- PostgreSQL database dump
--

\restrict 2dEsnRDkZqh8Joa7sYmhASNNjcBTmMgSvfDpIKWdvltktxeOobOPzZluzPQk0ee

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: consentements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.consentements (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    medecin_id integer NOT NULL,
    accord boolean DEFAULT false NOT NULL,
    date_consentement timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: consentements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.consentements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: consentements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.consentements_id_seq OWNED BY public.consentements.id;


--
-- Name: demandes_medecin; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.demandes_medecin (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    medecin_id integer NOT NULL,
    type_demande character varying(20) DEFAULT 'principal'::character varying NOT NULL,
    origine character varying(20) DEFAULT 'patient'::character varying NOT NULL,
    statut character varying(20) DEFAULT 'EN_ATTENTE'::character varying NOT NULL,
    message text,
    date_demande timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    date_reponse timestamp without time zone,
    date_rendez_vous date,
    heure_rendez_vous time without time zone,
    CONSTRAINT demandes_medecin_origine_check CHECK (((origine)::text = ANY ((ARRAY['patient'::character varying, 'medecin'::character varying])::text[]))),
    CONSTRAINT demandes_medecin_statut_check CHECK (((statut)::text = ANY ((ARRAY['EN_ATTENTE'::character varying, 'ACCEPTEE'::character varying, 'REFUSEE'::character varying])::text[]))),
    CONSTRAINT demandes_medecin_type_demande_check CHECK (((type_demande)::text = ANY ((ARRAY['principal'::character varying, 'specialiste'::character varying])::text[])))
);



--
-- Name: demandes_medecin_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.demandes_medecin_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: demandes_medecin_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.demandes_medecin_id_seq OWNED BY public.demandes_medecin.id;


--
-- Name: dossiers_medicaux; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dossiers_medicaux (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    contenu_chiffre text NOT NULL,
    date_creation timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    date_modification timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: dossiers_medicaux_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dossiers_medicaux_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: dossiers_medicaux_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dossiers_medicaux_id_seq OWNED BY public.dossiers_medicaux.id;


--
-- Name: jetons_reinitialisation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.jetons_reinitialisation (
    id integer NOT NULL,
    utilisateur_id integer NOT NULL,
    jeton_hash text NOT NULL,
    date_creation timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    date_expiration timestamp without time zone NOT NULL,
    utilise boolean DEFAULT false
);



--
-- Name: jetons_reinitialisation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.jetons_reinitialisation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: jetons_reinitialisation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.jetons_reinitialisation_id_seq OWNED BY public.jetons_reinitialisation.id;


--
-- Name: journal_audit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.journal_audit (
    id integer NOT NULL,
    utilisateur_id integer,
    action character varying(255) NOT NULL,
    ressource character varying(255),
    adresse_ip character varying(45),
    date_action timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: journal_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.journal_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: journal_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.journal_audit_id_seq OWNED BY public.journal_audit.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    utilisateur_id integer NOT NULL,
    type character varying(50) NOT NULL,
    message text NOT NULL,
    lue boolean DEFAULT false NOT NULL,
    date_creation timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: recommandations_specialiste; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.recommandations_specialiste (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    medecin_principal_id integer NOT NULL,
    specialiste_id integer NOT NULL,
    message text,
    statut character varying(20) DEFAULT 'EN_ATTENTE'::character varying NOT NULL,
    date_recommandation timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    date_reponse timestamp without time zone,
    CONSTRAINT recommandations_specialiste_statut_check CHECK (((statut)::text = ANY ((ARRAY['EN_ATTENTE'::character varying, 'ACCEPTEE'::character varying, 'REFUSEE'::character varying])::text[])))
);



--
-- Name: recommandations_specialiste_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.recommandations_specialiste_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: recommandations_specialiste_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.recommandations_specialiste_id_seq OWNED BY public.recommandations_specialiste.id;


--
-- Name: relations_patient_medecin; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.relations_patient_medecin (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    medecin_id integer NOT NULL,
    type_relation character varying(20) NOT NULL,
    actif boolean DEFAULT true NOT NULL,
    date_debut timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    date_fin timestamp without time zone,
    CONSTRAINT relations_patient_medecin_type_relation_check CHECK (((type_relation)::text = ANY ((ARRAY['principal'::character varying, 'specialiste'::character varying])::text[])))
);



--
-- Name: relations_patient_medecin_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.relations_patient_medecin_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: relations_patient_medecin_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.relations_patient_medecin_id_seq OWNED BY public.relations_patient_medecin.id;


--
-- Name: utilisateurs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.utilisateurs (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    role character varying(20) NOT NULL,
    actif boolean DEFAULT true,
    date_creation timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    nom character varying(100),
    prenom character varying(100),
    telephone character varying(30)
);



--
-- Name: utilisateurs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.utilisateurs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: utilisateurs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.utilisateurs_id_seq OWNED BY public.utilisateurs.id;


--
-- Name: consentements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consentements ALTER COLUMN id SET DEFAULT nextval('public.consentements_id_seq'::regclass);


--
-- Name: demandes_medecin id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.demandes_medecin ALTER COLUMN id SET DEFAULT nextval('public.demandes_medecin_id_seq'::regclass);


--
-- Name: dossiers_medicaux id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dossiers_medicaux ALTER COLUMN id SET DEFAULT nextval('public.dossiers_medicaux_id_seq'::regclass);


--
-- Name: jetons_reinitialisation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jetons_reinitialisation ALTER COLUMN id SET DEFAULT nextval('public.jetons_reinitialisation_id_seq'::regclass);


--
-- Name: journal_audit id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_audit ALTER COLUMN id SET DEFAULT nextval('public.journal_audit_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: recommandations_specialiste id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations_specialiste ALTER COLUMN id SET DEFAULT nextval('public.recommandations_specialiste_id_seq'::regclass);


--
-- Name: relations_patient_medecin id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.relations_patient_medecin ALTER COLUMN id SET DEFAULT nextval('public.relations_patient_medecin_id_seq'::regclass);


--
-- Name: utilisateurs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs ALTER COLUMN id SET DEFAULT nextval('public.utilisateurs_id_seq'::regclass);


--
-- Name: consentements consentements_patient_id_medecin_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consentements
    ADD CONSTRAINT consentements_patient_id_medecin_id_key UNIQUE (patient_id, medecin_id);


--
-- Name: consentements consentements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consentements
    ADD CONSTRAINT consentements_pkey PRIMARY KEY (id);


--
-- Name: demandes_medecin demandes_medecin_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.demandes_medecin
    ADD CONSTRAINT demandes_medecin_pkey PRIMARY KEY (id);


--
-- Name: dossiers_medicaux dossiers_medicaux_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dossiers_medicaux
    ADD CONSTRAINT dossiers_medicaux_pkey PRIMARY KEY (id);


--
-- Name: jetons_reinitialisation jetons_reinitialisation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jetons_reinitialisation
    ADD CONSTRAINT jetons_reinitialisation_pkey PRIMARY KEY (id);


--
-- Name: journal_audit journal_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_audit
    ADD CONSTRAINT journal_audit_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: recommandations_specialiste recommandations_specialiste_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations_specialiste
    ADD CONSTRAINT recommandations_specialiste_pkey PRIMARY KEY (id);


--
-- Name: relations_patient_medecin relations_patient_medecin_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.relations_patient_medecin
    ADD CONSTRAINT relations_patient_medecin_pkey PRIMARY KEY (id);


--
-- Name: utilisateurs utilisateurs_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_email_key UNIQUE (email);


--
-- Name: utilisateurs utilisateurs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilisateurs
    ADD CONSTRAINT utilisateurs_pkey PRIMARY KEY (id);


--
-- Name: unique_medecin_principal_actif; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX unique_medecin_principal_actif ON public.relations_patient_medecin USING btree (patient_id) WHERE (((type_relation)::text = 'principal'::text) AND (actif = true));


--
-- Name: unique_recommandation_specialiste_attente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX unique_recommandation_specialiste_attente ON public.recommandations_specialiste USING btree (patient_id, medecin_principal_id, specialiste_id) WHERE ((statut)::text = 'EN_ATTENTE'::text);


--
-- Name: consentements consentements_medecin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consentements
    ADD CONSTRAINT consentements_medecin_id_fkey FOREIGN KEY (medecin_id) REFERENCES public.utilisateurs(id);


--
-- Name: consentements consentements_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.consentements
    ADD CONSTRAINT consentements_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.utilisateurs(id);


--
-- Name: demandes_medecin demandes_medecin_medecin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.demandes_medecin
    ADD CONSTRAINT demandes_medecin_medecin_id_fkey FOREIGN KEY (medecin_id) REFERENCES public.utilisateurs(id);


--
-- Name: demandes_medecin demandes_medecin_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.demandes_medecin
    ADD CONSTRAINT demandes_medecin_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.utilisateurs(id);


--
-- Name: dossiers_medicaux dossiers_medicaux_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dossiers_medicaux
    ADD CONSTRAINT dossiers_medicaux_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.utilisateurs(id);


--
-- Name: jetons_reinitialisation fk_jeton_utilisateur; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jetons_reinitialisation
    ADD CONSTRAINT fk_jeton_utilisateur FOREIGN KEY (utilisateur_id) REFERENCES public.utilisateurs(id) ON DELETE CASCADE;


--
-- Name: journal_audit journal_audit_utilisateur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.journal_audit
    ADD CONSTRAINT journal_audit_utilisateur_id_fkey FOREIGN KEY (utilisateur_id) REFERENCES public.utilisateurs(id);


--
-- Name: notifications notifications_utilisateur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_utilisateur_id_fkey FOREIGN KEY (utilisateur_id) REFERENCES public.utilisateurs(id);


--
-- Name: recommandations_specialiste recommandations_specialiste_medecin_principal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations_specialiste
    ADD CONSTRAINT recommandations_specialiste_medecin_principal_id_fkey FOREIGN KEY (medecin_principal_id) REFERENCES public.utilisateurs(id);


--
-- Name: recommandations_specialiste recommandations_specialiste_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations_specialiste
    ADD CONSTRAINT recommandations_specialiste_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.utilisateurs(id);


--
-- Name: recommandations_specialiste recommandations_specialiste_specialiste_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recommandations_specialiste
    ADD CONSTRAINT recommandations_specialiste_specialiste_id_fkey FOREIGN KEY (specialiste_id) REFERENCES public.utilisateurs(id);


--
-- Name: relations_patient_medecin relations_patient_medecin_medecin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.relations_patient_medecin
    ADD CONSTRAINT relations_patient_medecin_medecin_id_fkey FOREIGN KEY (medecin_id) REFERENCES public.utilisateurs(id);


--
-- Name: relations_patient_medecin relations_patient_medecin_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.relations_patient_medecin
    ADD CONSTRAINT relations_patient_medecin_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.utilisateurs(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 2dEsnRDkZqh8Joa7sYmhASNNjcBTmMgSvfDpIKWdvltktxeOobOPzZluzPQk0ee

