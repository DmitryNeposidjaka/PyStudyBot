// берём Express
var express = require('express');

// создаём Express-приложение
var app = express();

// создаём маршрут для главной страницы
// http://localhost:8080/
app.get('/', function(req, res) {
  res.sendfile('index.html');
});
app.use('/assets', express.static('assets'));
app.use('/node_modules', express.static('node_modules'));

// запускаем сервер а порту 8080
app.listen(8080);
// отправляем сообщение
console.log('Сервер стартовал!');