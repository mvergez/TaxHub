#!/bin/bash

set -o pipefail

# Make sure only root can run our script
if [ "$(id -u)" == 0 ]; then
   echo "This script must not be run as root" 1>&2
   exit 1
fi


#Création des répertoires systèmes
. create_sys_dir.sh
create_sys_dir

if [ ! -f settings.ini ]; then
  cp settings.ini.sample settings.ini
fi

nano settings.ini

#include user config = settings.ini
. settings.ini

#get app path
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
LOG_DIR=$DIR/var/log


function database_exists () {
    # /!\ Will return false if psql can't list database. Edit your pg_hba.conf
    # as appropriate.
    if [ -z $1 ]
        then
        # Argument is null
        return 0
    else
        # Grep db name in the list of database
        sudo -u postgres -s -- psql -tAl | grep -q "^$1|"
        return $?
    fi
}


if database_exists $db_name
then
        if $drop_apps_db
            then
            echo "Suppression de la base..."
            sudo -u postgres -s dropdb $db_name
        else
            echo "La base de données existe et le fichier de settings indique de ne pas la supprimer."
        fi
fi
if ! database_exists $db_name
then
    echo "Création de la base..."
    sudo -u postgres -s createdb -O $user_pg $db_name

    sudo -n -u postgres -s psql -d $db_name -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" &> $LOG_DIR/installdb/install_db.log

    sudo -n -u postgres -s psql -d $db_name -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' &>> $LOG_DIR/installdb/install_db.log

    sudo -n -u postgres -s psql -d $db_name -c 'CREATE EXTENSION IF NOT EXISTS "pg_trgm";' &>> $LOG_DIR/installdb/install_db.log

    sudo -n -u postgres -s psql -d $db_name -c 'CREATE EXTENSION IF NOT EXISTS "unaccent";' &>> $LOG_DIR/installdb/install_db.log

    # Mise en place de la structure de la base et des données permettant son fonctionnement avec l'application

    source venv/bin/activate

    if [ $users_schema != "local" ]; then
        echo "Connexion à la base Utilisateur..."
        cp data/create_fdw_utilisateurs.sql /tmp/taxhub/create_fdw_utilisateurs.sql
        cp data/grant.sql /tmp/taxhub/grant.sql
        sed -i "s#\$user_pg#$user_pg#g" /tmp/taxhub/create_fdw_utilisateurs.sql
        sed -i "s#\$usershub_host#$usershub_host#g" /tmp/taxhub/create_fdw_utilisateurs.sql
        sed -i "s#\$usershub_db#$usershub_db#g" /tmp/taxhub/create_fdw_utilisateurs.sql
        sed -i "s#\$usershub_port#$usershub_port#g" /tmp/taxhub/create_fdw_utilisateurs.sql
        sed -i "s#\$usershub_user#$usershub_user#g" /tmp/taxhub/create_fdw_utilisateurs.sql
        sed -i "s#\$usershub_pass#$usershub_pass#g" /tmp/taxhub/create_fdw_utilisateurs.sql
        sed -i "s#\$usershub_user#$usershub_user#g" /tmp/taxhub/grant.sql
        sudo -u postgres -s psql -d $db_name -f /tmp/taxhub/create_fdw_utilisateurs.sql  &>> $LOG_DIR/installdb/install_db.log
        sudo -u postgres -s psql -d $db_name -f /tmp/taxhub/grant.sql  &>> $LOG_DIR/installdb/install_db.log
        flask db stamp 72f227e37bdf  # utilisateurs-samples
    fi

    flask db upgrade taxonomie_inpn_data@head -x data-directory=tmp/
    flask db upgrade taxhub-admin@head

    if $insert_geonatureatlas_data
    then
        echo "Insertion de données nécessaires à GeoNature-atlas"
        export PGPASSWORD=$user_pg_pass;psql -h $db_host -U $user_pg -d $db_name -f data/taxhubdata_atlas.sql  &>> $LOG_DIR/installdb/install_db.log
    fi

	if $insert_attribut_example
    then
        echo "Insertion d'un exemple d'attribut"
        flask db upgrade taxonomie_attributes_example@head
    fi

	if $insert_taxons_example
    then
        echo "Insertion de 8 taxons exemple"
        flask db upgrade taxonomie_taxons_example@head
    fi

    flask db upgrade taxonomie@head

    # Vaccum database
    echo "Vaccum database ... (cette opération peut être longue)"
    export PGPASSWORD=$user_pg_pass;psql -h $db_host -U $user_pg -d $db_name -c "VACUUM FULL VERBOSE;"  &>> $LOG_DIR/installdb/install_db.log

fi
