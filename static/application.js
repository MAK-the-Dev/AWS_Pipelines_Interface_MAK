$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var numbers_received = [];

    //receive details from socket server
    socket.on('newStatus', function(msg) {
        console.log("Received Status: " + msg.status + " Received name: " + msg.name);

        status_string = msg.status;

        var table = document.getElementById("tbl");

        for (var i = 0 ; i < table.rows.length; i++)
        {
            console.log(table.rows[i].cells[1].innerHTML)
            if (table.rows[i].cells[1].innerHTML==msg.name)
            {
                console.log("inside IF "+ table.rows[i].cells[1].innerHTML);
                table.rows[i].cells[3].innerHTML=status_string;
//                 $('#log').html(status_string);
            }
        }

    });

});