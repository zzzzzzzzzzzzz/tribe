-- script to init n8n db (can run from adminer)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'n8ndbuser') THEN
    CREATE ROLE "n8ndbuser" LOGIN PASSWORD '<your-strong-password>';
  ELSE
    ALTER ROLE "n8ndbuser" WITH LOGIN PASSWORD '<your-strong-password>';
  END IF;
END$$;

--

CREATE DATABASE "n8ndb" OWNER "n8ndbuser" ENCODING 'UTF8';

--
CREATE SCHEMA IF NOT EXISTS n8n AUTHORIZATION "n8ndbuser";
GRANT ALL PRIVILEGES ON SCHEMA n8n TO "n8ndbuser";
ALTER ROLE "n8ndbuser" IN DATABASE "n8ndb" SET search_path TO n8n, public;

-- verify
SELECT current_database(), current_user, current_schema();
SHOW search_path;
SELECT datname, pg_get_userbyid(datdba) AS owner FROM pg_database WHERE datname='n8ndb';
SELECT nspname, pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname='n8n';
