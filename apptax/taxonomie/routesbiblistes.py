#coding: utf8
from flask import jsonify, json, Blueprint, request, Response, make_response
import os, csv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, or_

from ..utils.utilssqlalchemy import json_resp
from .models import BibListes, CorNomListe, Taxref,BibNoms

from pypnusershub import routes as fnauth

db = SQLAlchemy()
adresses = Blueprint('bib_listes', __name__)


@adresses.route('/', methods=['GET'])
@json_resp
def get_biblistes(id = None):
        data = db.session.query(BibListes).order_by(BibListes.nom_liste).all()
        maliste = []
        for l in data:
            d = l.as_dict()
            d['nb_taxons'] = len(l.cnl)
            maliste.append(d)
        return maliste


@adresses.route('/<regne>', methods=['GET'])
@adresses.route('/<regne>/<group2_inpn>', methods=['GET'])
@json_resp
def get_biblistesbyTaxref(regne, group2_inpn = None):
    q = db.session.query(BibListes)
    if regne :
        q = q.filter(or_(BibListes.regne == regne, BibListes.regne == None))
    if group2_inpn :
        q = q.filter(or_(BibListes.group2_inpn == group2_inpn, BibListes.group2_inpn == None))
    results = q.all()
    return [liste.as_dict() for liste in results]

# Information de la liste et liste des taxons d'une liste
@adresses.route('/info/<int:idliste>', methods=['GET'])
@json_resp
def getOne_biblistesInfo(idliste = None):
    data_liste = db.session.query(BibListes).filter_by(id_liste=idliste).first()
    nom_liste = data_liste.as_dict()

    data = db.session.query(BibNoms,
    Taxref.nom_complet, Taxref.regne, Taxref.group2_inpn).\
    filter(BibNoms.cd_nom == Taxref.cd_nom).\
    filter(BibNoms.id_nom == CorNomListe.id_nom).\
    filter(CorNomListe.id_liste == idliste)

    taxons = data.all()
    results = []
    for row in taxons:
        data_as_dict = row.BibNoms.as_dict()
        data_as_dict['nom_complet'] = row.nom_complet
        data_as_dict['regne'] = row.regne
        data_as_dict['group2_inpn'] = row.group2_inpn
        results.append(data_as_dict)
    return  [nom_liste,results]


# Compter le nombre d'enregistrements dans biblistes
@adresses.route('/nblistes', methods=['GET'])
@json_resp
def getCount_biblistes():
    """
        retourne le nombre de liste contenu dans la table bib_liste
    """
    return db.session.query(BibListes).count()

# Compter le nombre de taxons dans une liste
@adresses.route('/countnoms/<int:idliste>', methods=['GET'])
@json_resp
def getCountNoms_biblistes(idliste = None):
    """
        retourne le nombre de nom associé à la liste idliste
    """
    data_liste = db.session.query(BibListes).filter_by(id_liste=idliste).first()
    print(data_liste.cnl)
    return len(data_liste.cnl)


# Exporter les taxons d'une liste dans un fichier csv
@adresses.route('/exportnoms/<int:idliste>', methods=['GET'])
@json_resp
def getExporter_biblistes(idliste = None):
    data = db.session.query(Taxref).\
    filter(BibNoms.cd_nom == Taxref.cd_nom).filter(BibNoms.id_nom == CorNomListe.id_nom).\
    filter(CorNomListe.id_liste == idliste).all()
    return [nom.as_dict() for nom in data]


######## Route pour module edit and create biblistes ##############################################

# Get data of list by id
@adresses.route('/<int:idliste>', methods=['GET'])
@json_resp
def getOne_biblistes(idliste = None):
    data = db.session.query(BibListes).filter_by(id_liste=idliste).first()
    return data.as_dict()


# Get list of picto in repertory ./static/images/pictos
@adresses.route('/pictosprojet', methods=['GET'])
@json_resp
def getPictos_files():
    pictos = os.listdir("./static/images/pictos")
    pictos.sort()
    return pictos


# Get list of picto in bib_listes table
@adresses.route('/pictos', methods=['GET'])
@json_resp
def getPictos_biblistes():
    pictos = db.session.query(BibListes.picto).distinct().order_by(BibListes.picto).all()
    return [picto[0] for picto in pictos]


# Get list of nom_liste in bib_listes table
@adresses.route('/nomlistes', methods=['GET'])
@json_resp
def getNomlistes_biblistes():
    nom_liste = db.session.query(BibListes.nom_liste).distinct().order_by(BibListes.nom_liste).all()
    return [nom[0] for nom in nom_liste]


# Get list of id_liste in bib_listes table
@adresses.route('/idlistes', methods=['GET'])
@json_resp
def getIdlistes_biblistes():
    ids = db.session.query(BibListes.id_liste).order_by(BibListes.id_liste).all()
    return [i[0] for i in ids]


######### PUT CREER/MODIFIER BIBLISTES ######################
@adresses.route('/', methods=['POST','PUT'])
@adresses.route('/<int:id_liste>', methods=['POST', 'PUT'])
@json_resp
@fnauth.check_auth(4, True)
def insertUpdate_biblistes(id_liste=None, id_role=None):
    res = request.get_json(silent=True)
    data = {k:v or None for (k,v) in res.items()}
    bib_liste = BibListes(**data)
    db.session.merge(bib_liste)
    try:
        db.session.commit()
        return bib_liste.as_dict()
    except Exception as e:
        db.session.rollback()
        return ({'success':False, 'message':'Impossible de sauvegarder l\'enregistrement'}, 500)


######## Route pour module ajouter noms à la liste ##############################################
## Get Taxons + taxref in a liste with id_liste
@adresses.route('/taxons/', methods=['GET'])
@adresses.route('/taxons/<int:idliste>', methods=['GET'])
@json_resp
def getNoms_bibtaxons(idliste = None):
    q = db.session.query(BibNoms,
        Taxref.nom_complet, Taxref.regne, Taxref.group2_inpn).\
        filter(BibNoms.cd_nom == Taxref.cd_nom)

    if (idliste) :
        q = q.filter(BibNoms.id_nom == CorNomListe.id_nom).\
        filter(CorNomListe.id_liste == idliste)

    data = q.all()
    results = []
    for row in data:
        data_as_dict = row.BibNoms.as_dict()
        data_as_dict['nom_complet'] = row.nom_complet
        data_as_dict['regne'] = row.regne
        data_as_dict['group2_inpn'] = row.group2_inpn
        results.append(data_as_dict)
    return results


## POST - Ajouter les noms à une liste
@adresses.route('/addnoms/<int:idliste>', methods=['POST'])
@json_resp
@fnauth.check_auth(4, True)
def add_cornomliste(idliste = None,id_role=None):
    ids_nom = request.get_json(silent=True)
    data = db.session.query(CorNomListe).filter(CorNomListe.id_liste == idliste).all()
    for id in ids_nom:
        cornom = {'id_nom':id,'id_liste':idliste}
        add_nom = CorNomListe(**cornom)
        db.session.add(add_nom)
    try:
        db.session.commit()
        return ids_nom
    except Exception as e:
        db.session.rollback()
        return ({'success':False, 'message':'Impossible de sauvegarder l\'enregistrement'}, 500)


## POST - Enlever les nom dans une liste
@adresses.route('/deletenoms/<int:idliste>', methods=['POST'])
@json_resp
@fnauth.check_auth(4, True)
def delete_cornomliste(idliste = None,id_role=None):
    ids_nom = request.get_json(silent=True)
    for id in ids_nom:
        del_nom =db.session.query(CorNomListe).filter(CorNomListe.id_liste == idliste).\
        filter(CorNomListe.id_nom == id).first()
        db.session.delete(del_nom)
    try:
        db.session.commit()
        return ids_nom
    except Exception as e:
        db.session.rollback()
        return ({'success':False, 'message':'Impossible de sauvegarder l\'enregistrement'}, 500)
