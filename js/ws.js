let ws = new WebSocket("ws://localhost:8765");

ws.onopen = function (e) {
    console.log("[open] Connection established");
    setTimeout(() => {
        document.getElementById("pageloader_title").innerHTML = "Connected!";
    }, 1000);

    setTimeout(() => {
        document.getElementById("pageloader").classList.remove('is-active');
    }, 2000);

};

ws.onmessage = function (event) {
    console.log(`[message] Data received from server: ${event.data}`);
};

ws.onclose = function (event) {
    document.getElementById("notification_disconnected").classList.remove('is-hidden');
    // if (event.wasClean) {
    //     alert(
    //         `[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`
    //     );
    // } else {
    //     // e.g. server process killed or network down
    //     // event.code is usually 1006 in this case
    //     alert("[close] Connection died");
    // }
};

ws.onerror = function (error) {
    alert(`[error] ${error.message}`);
};

function send_code(code) {
    console.log(code)
    ws.send(code)
}

function send_custom_code(e) {
    if (e.keyCode == 13) {
        element = document.getElementById("custom_command")
        data = element.value
        element.value = ""
        console.log(data)
        ws.send(data)
    }
}

function send_gcode() {
    var file = document.getElementById('filename').files[0];

    ws.send("GCD")
    ws.send(file);
    alert("the File has been transferred.")
}