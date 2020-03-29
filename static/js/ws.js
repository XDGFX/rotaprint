// --- MAIN WEBSOCKET CONNECTIONS ---

let ws = new WebSocket("ws://localhost:8765");
response = "";

ws.onopen = function (e) {
    console.log("[open] Connection established");
    setTimeout(() => {
        document.getElementById("pageloader_title").innerHTML = "Connected!";
    }, 500);

    setTimeout(() => {
        document.getElementById("pageloader").classList.remove('is-active');
    }, 1000);
};


// MESSAGE RESPONSE HANDLER
ws.onmessage = function (event) {
    console.log(`[message] Data received from server: ${event.data}`);
    response = event.data.split("~")

    switch (response[0]) {
        case "GCD":
            send_gcode(response[1])
        case "FTS":
            update_settings(response[1])
        default:
            break;
    }
};


// CONNECTION CLOSE
ws.onclose = function (event) {
    setTimeout(() => {
        bulmaToast.toast({
            message: "Backend disconnected. Any further changes may not be applied. Attempt to <a href=\"\">reconnect?</a>",
            type: "is-danger",
            position: "bottom-right",
            duration: 99999999,
            closeOnClick: false,
            animate: { in: "fadeInRight", out: "fadeOutRight" }
        });
    }, 1000);
};


// CONNECTION ERROR
ws.onerror = function (error) {
    document.getElementById("pageloader_title").innerHTML = "An error occured while attempting to connect."
    document.getElementById("pageloader").classList.add('is-stopped');

    console.log(`[error] ${error.message}`);
};


// function send_code(code) {
//     console.log(code)
//     ws.send(code)
// }

// --- SPECIAL FUNCTIONS ---
function send_custom_code(e) {
    if (e.keyCode == 13) {
        element = document.getElementById("custom_command")
        data = element.value
        element.value = ""
        console.log(data)
        ws.send(data)
    }
}

// --- COMMAND FUNCTIONS ---
function send_gcode(data) {
    if (data == "done") {
        var fileName = document.querySelector('#gcode_uploader .file-name');
        fileName.classList.remove('has-text-grey-lighter');
        fileName.textContent = fileInput.files[0].name;

        // Send notification success
        bulmaToast.toast({
            message: "Backend received GCODE successfully",
            type: "is-success",
            position: "bottom-right",
            dismissible: true,
            closeOnClick: false,
            duration: 4000,
            animate: { in: "fadeInRight", out: "fadeOutRight" }
        });

        return
    }

    console.log("GCODE detected...")
    ws.send("GCD")
    ws.send(data.files[0]);
    console.log("The file has been sent...")

}

// Set default variable to make global
settings_table = ""

// Get settings from database and update form values
function update_settings(data) {
    // Send command
    if (data == null) {
        ws.send("FTS")
        return
    }
    // Handle response
    settings_table = JSON.parse(data)
    for (const key of Object.keys(settings_table)) {
        id = document.getElementById("setting_".concat(key))
        if (id != null) {
            id.value = settings_table[key]
        }
    }
}