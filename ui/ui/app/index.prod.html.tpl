<!DOCTYPE html>
<!--[if lt IE 7]>      <html lang="en" ng-app="trackit" class="no-js lt-ie9 lt-ie8 lt-ie7"> <![endif]-->
<!--[if IE 7]>         <html lang="en" ng-app="trackit" class="no-js lt-ie9 lt-ie8"> <![endif]-->
<!--[if IE 8]>         <html lang="en" ng-app="trackit" class="no-js lt-ie9"> <![endif]-->
<!--[if gt IE 8]><!-->
<html lang="en" ng-app="trackit" class="no-js">
<!--<![endif]-->

<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Trackit.IO</title>
  <meta name="description" content="">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" type="image/png" href="favicon.png">
  <link rel="stylesheet" href="bower_components/html5-boilerplate/dist/css/normalize.css">
  <link rel="stylesheet" href="bower_components/html5-boilerplate/dist/css/main.css">
  <link rel="image_src" href="img/logo.png">
  <script src="bower_components/html5-boilerplate/dist/js/vendor/modernizr-2.8.3.min.js"></script>

  <link href="https://fonts.googleapis.com/css?family=Montserrat:400,700" rel="stylesheet" type="text/css">
  <script src='https://www.google.com/recaptcha/api.js'></script>


  <!-- bower:css -->
  <!-- endbower -->
  <link rel="stylesheet" href="min.css">
</head>

<body>

  <!--[if lt IE 7]>
      <p class="browsehappy">You are using an <strong>outdated</strong> browser. Please <a href="http://browsehappy.com/">upgrade your browser</a> to improve your experience.</p>
  <![endif]-->

  <ui-view></ui-view>


  <!-- Bower components -->
  <!-- bower:js -->
  <!-- endbower -->
  <script src="/bower_components/countUp.js/dist/angular-countUp.min.js"></script>
  <script src="min.js"></script>

  <!-- Non angular js -->
  <!-- include: "type": "js", "files": "js/**/*.js" -->

  <script src="config.js"></script>

  <script>
    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
    (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
    m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
    })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

    ga('create', 'UA-79880919-1', 'auto');
    ga('send', 'pageview');
    $(window).on('hashchange', function() {
        ga('set', 'page', document.location.toString().split(document.location.hostname).reverse()[0]);
        ga('send', 'pageview');
    });

  </script>
</body>

</html>
