'use strict';

// Config Module
var trackitConfig = angular.module('trackit.config', []);

// Factory to get API Url from the controllers
trackitConfig.factory("Config", ['$location', function($location) {
    var config = {};

    if (window.TRACKIT_CONFIG && TRACKIT_CONFIG.apiBaseUrl) {
        config.apiBaseUrl = TRACKIT_CONFIG.apiBaseUrl;
    }

    if (window.TRACKIT_CONFIG && TRACKIT_CONFIG.enableForgottenPassword) {
        config.enableForgottenPassword = TRACKIT_CONFIG.enableForgottenPassword;
    }

    if (window.TRACKIT_CONFIG && TRACKIT_CONFIG.loginOnlyEmail) {
        config.loginOnlyEmail = TRACKIT_CONFIG.loginOnlyEmail;
    }

    if (!config.apiBaseUrl) {
        // Get current URL and use port 5000 as API Url
        config.apiBaseUrl = [$location.protocol(), '://', $location.host(), ':', 5000].join('');
        //Uncomment next line if the UI is running locally and you want to force API Url
        //config.apiBaseUrl = "https://api.trackit.io";
    }
    config.apiUrl = function(route) {
        return this.apiBaseUrl + route;
    };

    return config;
}]);

// Declare app level module which depends on views, and components
var trackit = angular.module('trackit', [
        'ngResource',
        'ngCookies',
        'ngAnimate',
        'ngMaterial',
        'nvd3',
        'vcRecaptcha',
        'ui.router',
        'ui.bootstrap',
        'uiSwitch',
        'trackit.config',
        'rzModule',
        'countUpModule',
        'trackit.menu',
        'trackit.home',
        'trackit.storage',
        'trackit.aws.services',
        'trackit.keyselect',
        'trackit.statistics',
        'trackit.prediction',
    ]).run(function($rootScope, $state, $cookies, $http) {
        // On each state change we check if the next state requires the user to be logged in
        $rootScope.$on('$stateChangeStart', function(event, toState, toParams) {
            var requireLogin = toState.data.requireLogin;

            // If the user token is not defined in the rootscope we search for it in the cookies
            if (!$rootScope.userToken) {
                var userCookie = $cookies.getObject('userToken');
                if (typeof userCookie != 'undefined') {
                    $rootScope.userToken = userCookie.token;
                    // We set usertoken as default header in all further HTTP requests
                    $http.defaults.headers.common['Authorization'] = userCookie.token;
                }
            }

            // User is not logged in
            if (requireLogin && typeof $rootScope.userToken === 'undefined') {
                event.preventDefault();
                $state.go('login');
            }

            // If the AWS key is not defined in the rootscope we search for it in the cookies
            if (!$rootScope.awsKey) {
                var awsKeyCookie = $cookies.getObject('awsKey');
                if (typeof awsKeyCookie != 'undefined') {
                    $rootScope.awsKey = awsKeyCookie;
                }
            }
            // We add AWS key to be in headers in further HTTP requests
            if (!$http.defaults.headers.common['User-AWS-Key']) {
                var awsKeyCookie = $cookies.getObject('awsKey');
                if (typeof awsKeyCookie != 'undefined') {
                    $http.defaults.headers.common['User-AWS-Key'] = awsKeyCookie;
                }
            }
        });
    }).config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
        // If URL is not in a defined state we redirect to /home
        $urlRouterProvider.otherwise(function() {
          window.location.href = TRACKIT_CONFIG.notFoundUrl;
        });

        // Defining all app states
        $stateProvider
            .state('authenticated', {
                url: '/authenticated?token&token_expires',
                template: '<p>Authenticated. Please wait.</p>',
                controller: function($stateParams, $state, $cookies, $rootScope, $http) {
                    var expires = new Date($stateParams.token_expires);
                    var token = $stateParams.token;

                    $cookies.putObject('userToken', {
                        token: token
                    }, {
                        expires: expires
                    });
                    $http.defaults.headers.common['Authorization'] = token;
                    $rootScope.userToken = token;
                    $state.go('app.keyselect');
                },
                data: {
                    requireLogin: false
                },
            })
            .state('signup', {
                url: "/signup",
                templateUrl: 'components/signup/signup.html',
                controller: "SignupCtrl",
                data: {
                    requireLogin: false
                }
            })
            .state('request-trial', {
                url: "/request-trial?demo",
                templateUrl: 'components/request-trial/request-trial.html',
                controller: "RequestTrialCtrl",
                data: {
                    requireLogin: false
                }
            })
            .state('login', {
                url: "/login",
                templateUrl: 'components/login/login.html',
                controller: "LoginCtrl",
                data: {
                    requireLogin: false
                }
            })
            .state('resetpassword', {
                url: "/lostpassword/:token",
                templateUrl: 'components/login/resetPassword.html',
                controller: "ResetPasswordCtrl",
                data: {
                    requireLogin: false
                }
            })
            // App master state, all children states will inherit requireLogin: true
            .state('app', {
                templateUrl: "appView.html",
                controller: "MenuCtrl",
                data: {
                    requireLogin: true // this property will apply to all children of 'app' state
                }
            })
            .state('app.keyselect', {
                url: "/app/keyselect?:fromLogin",
                templateUrl: "/components/keyselect/keyselect.html",
                controller: "KeyselectCtrl",
                data: {
                    requireLogin: true
                }
            })
            .state('app.home', {
                url: "/app/home/:key",
                templateUrl: "/components/home/home.html",
                controller: 'HomeCtrl',
                /*resolve: {
                    keyPair: ['$stateParams', 'AWSKey', '$http', '$cookies', '$rootScope',
                        function($stateParams, AWSKey, $http, $cookies, $rootScope) {
                            var keyRes = AWSKey.get({
                                id: $stateParams.key
                            }, function(data) {
                                var expires = new Date();
                                expires.setDate(expires.getDate() + 2);
                                console.log(data);
                                $rootScope.awsKey = data.id;
                                $cookies.putObject('awsKey', data.id, {
                                    expires: expires
                                });

                            }, function(data) {
                                console.log('error on key retrieval:')
                            });


                            return keyRes.$promise;
                        }
                    ]
                },*/
                data: {
                    requireLogin: true
                }
            })
            // Monitor
            .state('app.s3map', {
                url: "/app/s3map",
                templateUrl: "/components/s3map/s3mapView.html",
                controller: 'S3MapCtrl'
            })
            .state('app.monitor', {
                url: "/app/monitor",
                templateUrl: "/components/monitor/utilization/utilizationView.html",
                controller: 'UtilizationCtrl'
            })
            // Optimize
            .state('app.costestimation', {
                url: "/app/estimation?optprov&?selectedtab",
                templateUrl: "/components/optimize/costestimation/costEstimationView.html",
                controller: 'CostEstimationCtrl'
            })
            .state('app.prediction', {
                url: "/app/prediction",
                templateUrl: "/components/predict/prediction.html",
                controller: 'PredictionCtrl'
            })
            // Automate
            .state('app.cloudmover', {
                url: "/app/cloudmover",
                templateUrl: "/components/automate/cloudmover/cloudmoverView.html"
            })
            //// State enabling/disabling cloudmover feature
            .state('app.togglemover', {
                url: "/app/togglemover",
                templateUrl: "/components/automate/cloudmover/toggleCloudmover.html",
                controller: 'ToggleCloudmoverCtrl',
            })
            // Other
            .state('app.statistics', {
                url: "/app/statistics",
                templateUrl: "/components/statistics/statisticsView.html",
                controller: 'StatisticsCtrl',
            })
            .state('app.storage', {
                url: "/app/storage",
                templateUrl: "/components/storage/storage.html",
                controller: "StorageCtrl",
            })
            .state('app.treemap', {
                url: "/app/treemap",
                templateUrl: "/components/s3map/TreeMapView.html"
            })
            .state('app.automation', {
                url: "/app/automation",
                templateUrl: "/components/automation/automation.html"
            })
            .state('app.setupguide', {
                url: "/app/setupguide",
                controller: 'setupGuideviewCtrl',
                templateUrl: "/components/setup-guide/setupGuideview.html",
                data: {
                    requireLogin: false
                }
            })



    }])
    .config(['$httpProvider', function($httpProvider) {
        // Setup HTTP requests for CORS
        $httpProvider.defaults.useXDomain = true;
        delete $httpProvider.defaults.headers.common['X-Requested-With'];
    }])
    .factory('apiBaseUrl', ['$location', 'Config', function($location, Config) {
        return Config.apiBaseUrl;
    }]);

/* Multi Controllers Modules declaration */

angular.module('trackit.home', []);
angular.module('trackit.prediction', []);
angular.module('trackit.statistics', []);
angular.module('trackit.general', []);
