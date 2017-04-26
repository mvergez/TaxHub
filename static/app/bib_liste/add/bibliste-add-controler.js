app.controller('bibListeAddCtrl',[ '$scope','$filter', '$http','$uibModal','$route','$routeParams','NgTableParams','toaster','bibListeAddSrv', 'backendCfg','loginSrv',
  function($scope,$filter, $http,$uibModal,$route, $routeParams,NgTableParams,toaster,bibListeAddSrv, backendCfg,loginSrv) {
    var self = this;
    self.showSpinnerSelectList = true;
    self.showSpinner = true;
    self.isSelected = false;
    self.listName = {
    selectedList: {},
    availableOptions: {}
   };
    self.tableCols = {
      "nom_francais" : { title: "Nom français", show: true },
      "nom_complet" : {title: "Nom latin", show: true },
      "lb_auteur" : {title: "Auteur", show: true },
      "cd_nom" : {title: "cd nom", show: true },
      "id_nom" : {title: "id nom", show: true }
    };

    //----------------------Gestion des droits---------------//
    if (loginSrv.getCurrentUser()) {
        self.userRightLevel = loginSrv.getCurrentUser().id_droit_max;
        // gestion de l'onglet actif ; 0 par default
        if (self.userRightLevel==backendCfg.user_low_privilege) {
        self.activeForm = 2;
        }
    }
    self.userRights = loginSrv.getCurrentUserRights();
    //---------------------Get list of "nom de la Liste"---------------------
    bibListeAddSrv.getListOfNomsListes().then(
      function(res){
        self.listName.availableOptions = res;
        self.showSpinnerSelectList = false;
      });
    //---------------------Initialisation des paramètres de ng-table---------------------
    self.tableParams = new NgTableParams(
      {
          count: 50,
          sorting: {'nom_francais': 'asc'}
      }
    );
    //---------------------Get taxons------------------------------------
    self.getTaxons = function() {
      self.showSpinner = true;
      bibListeAddSrv.getbibNomsList().then(
        function(res) {
          self.showSpinner = false;
          self.tableParams.settings({dataset:res});
        }
      );
    };
    //--------------------- Selected Liste Change ---------------------
    self.listSelected = function(){
      self.isSelected = true;
      // Get taxons
      self.getTaxons();
    };

}]);

/*---------------------SERVICES : Appel à l'API bib_noms--------------------------*/
app.service('bibListeAddSrv', ['$http', '$q', 'backendCfg', function ($http, $q, backendCfg) {

    this.getbibNomsList = function () {
      var defer = $q.defer();
      $http.get(backendCfg.api_url+"biblistes/add/taxons").then(function successCallback(response) {
        defer.resolve(response.data);
      }, function errorCallback(response) {
        alert('Failed: ' + response);
      });
      return defer.promise;
    };

    this.getListOfNomsListes = function () {
      var defer = $q.defer();
      $http.get(backendCfg.api_url+"biblistes").then(function successCallback(response) {
        defer.resolve(response.data);
      }, function errorCallback(response) {
        alert('Failed: ' + response);
      });
      return defer.promise;
    };
}]);