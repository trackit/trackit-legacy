var express = require('express');
var morgan = require('morgan');
var fs = require('fs');
var bodyParser = require('body-parser');
var nodemailer = require("nodemailer");
var app = express();

app.use(express.static(__dirname + '/app')); // set the static files location /public/img will be /img for users
app.use(morgan('dev'));
app.use(bodyParser.urlencoded({
  'extended': 'true'
})); // parse application/x-www-form-urlencoded
app.use(bodyParser.json()); // parse application/json
app.use(bodyParser.json({
  type: 'application/vnd.api+json'
})); // parse application/vnd.api+json as json


var transporter = nodemailer.createTransport('smtps://sendtrackit%40gmail.com:trackit2016@smtp.gmail.com');



function readJSONFile(filename, callback) {
  fs.readFile(filename, function(err, data) {
    if (err) {
      callback(err);
      return;
    }
    try {
      callback(null, JSON.parse(data));
    } catch (exception) {
      callback(exception);
    }
  });
}

app.post('/send', function(req, res) {

  // setup e-mail data with unicode symbols
  var mailOptions = {
    from: '"Trackit Bot" <sendtrackit@gmail.com>', // sender address
    to: 'support@msolution.io', // list of receivers
    subject: 'Contact from Trackit.IO', // Subject line
    text: 'Name: '+ req.body.name + ' Email: '+req.body.email + ' Phone : ' + req.body.phone + ' Message : ' + req.body.message,
    html: 'Name: '+ req.body.name + '<br>Email: '+req.body.email + '<br>Phone : ' + req.body.phone + '<br><br>Message : <br>' + req.body.message
  };

  // send mail with defined transport object
  transporter.sendMail(mailOptions, function(error, info) {
    if (error) {
      res.end("error");
      return console.log(error);

    }
    res.end("sent");
    console.log('Message sent: ' + info.response);
  });


});



// listen (start app with node server.js) ======================================
var port = 8000;
app.listen(port);
console.log("[App listening on port " + port + ']');
