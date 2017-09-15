'use strict';

var module = angular.module('trackit.keyselect');

module.directive('googleKeyRegister', function () {
	return {
		template: [
			'<form action="{{gcloudUri}}" method="POST">',
			'	<p>{{gcloudUri}}</p>',
			'	<p>{{userToken}}</p>',
			'	<input name="token" type=hidden value="{{userToken}}">',
			'	<button type="submit" class="btn btn-default btn-google">Register Google account</button>',
			'</form>'
		].join(''),
	};
});
