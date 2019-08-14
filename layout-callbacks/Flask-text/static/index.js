$(document).ready(function() {
            // Use a "/test" namespace.
            // An application can open a connection on multiple namespaces, and
            // Socket.IO will multiplex all those connections on a single
            // physical channel. If you don't care about multiple channels, you
            // can set the namespace to an empty string.
            var namespace = '/test';

            // Connect to the Socket.IO server.
            // The connection URL has the following format, relative to the current page:
            //     http[s]://<domain>:<port>[/<namespace>]
            var socket = io(namespace);

            // Event handler for new connections.
            // The callback function is invoked when a connection with the
            // server is established.
            socket.on('connect', function() {
                socket.emit('connected', {data: 'I\'m connected!'});
            });

            // Event handler for server sent data.
            // The callback function is invoked whenever the server emits data
            // to the client. The data is then displayed in the "Received"
            // section of the page.

            socket.on('text_stream', function(msg) {
                var data = JSON.parse(msg.data);
                var value;  // значение параметра
                var length_table;  // ширина выводимых дынных
                var $log = $('#log');
                var newTR = document.createElement('tr');
                newTR.className = "line";
                $log.append(newTR);

                for (var key in data){
                    var newTD = document.createElement('td');
                    newTD.className = "column_key";
                    newTD.innerHTML = key +':';
                    newTR.append(newTD);

                    value = data[key];
                    newTD = document.createElement('td');
                    newTD.className = "column_value";
                    newTD.innerHTML = value + ',';
                    newTR.append(newTD);
                }
                var scrollTop = window.pageYOffset || document.documentElement.scrollTop; // cross-browser
                scrollTop = scrollTop + document.documentElement.clientHeight; // текущая прокрутка + высота окна
                if (document.body.scrollHeight - scrollTop < 50) {  // если пользователь не использовал scroll вверх
                    newTR.scrollIntoView(false); // прокручивает страницу до последнего элемента
                }
                length_table = newTR.offsetWidth;
                console.log(length_table);
            });



            // Interval function that tests message latency by sending a "ping"
            // message. The server then responds with a "pong" message and the
            // round trip time is measured.
            var ping_pong_times = [];
            var start_time;
            window.setInterval(function() {
                start_time = (new Date).getTime();
                socket.emit('ping');
            }, 1000);

            // Handler for the "pong" message. When the pong is received, the
            // time from the ping is stored, and the average of the last 30
            // samples is average and displayed.
            socket.on('pong', function() {
                var latency = (new Date).getTime() - start_time;
                ping_pong_times.push(latency);
                ping_pong_times = ping_pong_times.slice(-30); // keep last 30 samples
                var sum = 0;
                for (var i = 0; i < ping_pong_times.length; i++)
                    sum += ping_pong_times[i];
                $('#ping-pong').text(Math.round(10 * sum / ping_pong_times.length) / 10);
            });
            $('form#disconnect').submit(function(event) {
                socket.emit('disconnect_request');
                return false;
            });
        });