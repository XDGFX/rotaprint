// WEBSOCKET
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

    check_connected()
};

ws.onmessage = function (event) {
    console.log(`[message] Data received from server: ${event.data}`);
    data = JSON.parse(event.data)
    command = data["command"]
    payload = data["payload"]

    switch (command) {
        case "GCD":
            send_gcode(payload);
            break
        case "FTS":
            update_settings(payload);
            break
        case "RQV":
            check_connected(payload);
            break
        case "DBS":
            send_new_settings(payload);
            break
        case "ECO":
            echo_chamber(payload);
            break
    }
};

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

ws.onerror = function (error) {
    document.getElementById("pageloader_title").innerHTML = "An error occured while attempting to connect."
    document.getElementById("pageloader").classList.add('is-stopped');

    console.log(`[error] ${error.message}`);
};


// COMMANDS
function payloader(command, payload) {
    data = {
        "command": String(command),
        "payload": String(payload)
    }

    data = JSON.stringify(data)
    return data
}

function echo_chamber(payload) {
    console.log(payload)
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

function send_gcode(data) {
    if (data == "done") {
        var fileName = document.querySelector('#gcode_uploader .file-name');
        fileName.classList.remove('has-text-grey-lighter');
        fileName.textContent = fileInput.files[0].name;

        // Send notification success
        bulmaToast.toast({
            message: "Backend received GCODE successfully!",
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
    ws.send(payloader("GCD", data.files[0]))
    console.log("The file has been sent...")

}

// DATABASE
// Set default variable to make global
var settings_table = ""
function update_settings(data) {
    // Get settings from database and update form values

    // Send command
    if (data == null) {
        ws.send(payloader("FTS"))
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

var commit_settings = {};
function send_new_settings(data) {
    switch (data) {
        case "CONFIRM":
            send_data = JSON.stringify(commit_settings)
            ws.send(payloader("DBS", send_data))
            return

        case "CHECK":
            commit_settings = {};
            html = ""
            invalid_data = false
            for (var i = 0; i < changed.length; i++) {
                name = changed[i].id.replace("setting_", "")
                new_value = changed[i].value
                commit_settings[name] = new_value
                if (new_value == "") {
                    new_value = "INVALID"
                    invalid_data = true
                }
                html = html.concat("<tr><th>", name, "</th><td><code>", settings_table[name], "</code></td><td><code>", new_value, "</code></td></tr>")
            }

            tb = document.getElementById("updated_settings_table")
            tb.innerHTML = html
            show_help("modal_confirm_settings")

            confirm_button = document.getElementById("confirm_settings_button")
            if (!invalid_data) {
                confirm_button.disabled = false
                confirm_button.innerHTML = "Save changes"
            } else {
                confirm_button.disabled = true
                confirm_button.innerHTML = "Invalid Data"
            }
            return

        case "DONE":
            // Send notification success
            bulmaToast.toast({
                message: "Database updated successfully!",
                type: "is-success",
                position: "bottom-right",
                dismissible: true,
                closeOnClick: false,
                duration: 4000,
                animate: { in: "fadeInRight", out: "fadeOutRight" }
            });
            return

        case "ERROR":
            bulmaToast.toast({
                message: "Failed to update database.",
                type: "is-danger",
                position: "bottom-right",
                dismissible: true,
                closeOnClick: false,
                duration: 99999999,
                animate: { in: "fadeInRight", out: "fadeOutRight" }
            });
            return
    }
}


// PRINTER
function check_connected(data) {
    if (data == "False") {
        // Send notification error
        bulmaToast.toast({
            message: "Could not connect to printer... <a onclick=\"reconnect_printer()\">Retry?</a>",
            type: "is-danger",
            position: "bottom-right",
            dismissible: true,
            closeOnClick: false,
            duration: 99999999,
            animate: { in: "fadeInRight", out: "fadeOutRight" }
        });
        return
    } else if (data == "True") {
        // Send notification success
        bulmaToast.toast({
            message: "Printer connected successfully!",
            type: "is-success",
            position: "bottom-right",
            dismissible: true,
            closeOnClick: false,
            duration: 4000,
            animate: { in: "fadeInRight", out: "fadeOutRight" }
        });
        return
    }

    console.log("Checking printer connection...")
    // ws.send(payloader("RQV", "connected")
}

function reconnect_printer() {
    ws.send("RCN")
    setTimeout(() => {
        check_connected("");
    }, 1000);
}


// HELP
function show_help(which) {
    document.getElementById(which).classList.add('is-active');
    modal_animation()
}

function hide_help(which) {
    id = which.parentElement.id
    document.getElementById(id).classList.remove('is-active');
}


// SETTINGS
function show_settings() {
    element = document.getElementById("machine_settings")
    element.classList.remove('animated', 'slideOutRight');
    element.classList.add('animated', 'slideInRight');
    element.classList.remove('is-hidden');
    document.getElementById("settings_apply").disabled = true
    document.getElementById("settings_apply").innerHTML = "Apply Settings"
    update_settings()
}

function hide_settings(saved) {
    if (saved == false) {
        console.log("Are you sure?")
    }
    element = document.getElementById("machine_settings")
    element.classList.remove('animated', 'slideInRight');
    element.classList.add('animated', 'slideOutRight');
    setTimeout(() => {
        element.classList.add('is-hidden');

        // Remove changed warning icons on all settings
        changed = element.querySelectorAll(".is-warning");

        for (var i = 0; i < changed.length; i++) {
            changed[i].classList.remove('is-warning')
        }

    }, 900);
}

function toggle_advanced_settings() {
    checked = document.getElementById("switch_advanced_settings").checked
    advanced = document.getElementById("settings_column").querySelectorAll(".advanced_setting");

    for (var i = 0; i < advanced.length; i++) {
        advanced[i].disabled = !checked

        // if (advanced[i].localName == "fieldset" && !checked) {
        //     input = advanced[i].querySelectorAll([id ^= 'setting_'])
        // }

    }

    field = document.getElementById("advanced_settings_field")
    if (checked) {
        field.classList.remove("has-text-grey-lighter")
        field.classList.add("has-text-danger")
    } else {
        field.classList.add("has-text-grey-lighter")
        field.classList.remove("has-text-danger")
    }
}

changed = ""
function check_changed(element) {
    id = element.id.split("_")[1]

    old_value = String(settings_table[id])
    current_value = element.value

    if (old_value == current_value) {
        element.classList.remove("is-warning")
    } else {
        element.classList.add("is-warning")
    }

    settings_element = document.getElementById("machine_settings")

    // Remove changed warning icons on all settings
    changed = document.getElementById("machine_settings").querySelectorAll(".is-warning");
    button = document.getElementById("settings_apply")

    if (changed.length > 0) {
        button.disabled = false
        if (changed.length > 1) {
            button.innerHTML = "Apply " + changed.length + " Settings"
        } else {
            button.innerHTML = "Apply " + changed.length + " Setting"
        }

    } else {
        button.disabled = true
        button.innerHTML = "Apply Settings"
    }

}

function set_default(input_id) {
    var defaults = {
        "$0": 10, // Length of step pulse, microseconds
        "$1": 255, // Step idle delay, milliseconds
        "$2": 0, // Step port invert, mask
        "$3": 0, // Direction port invert, mask
        "$4": 0, // Step enable invert, boolean
        "$5": 0, // Limit pins invert, boolean
        "$6": 0, // Probe pin invert, boolean
        "$10": 1, // Status report, mask
        "$11": 0.010, // Junction deviation, mm
        "$12": 0.002, // Arc tolerance, mm
        "$13": 0, // Report inches, boolean
        "$20": 0, // Soft limits, boolean !!! Should be enabled for real use
        "$21": 0,       // Hard limits, boolean
        "$22": 1,       // Homing cycle, boolean
        "$23": 0,       // Homing dir invert, mask
        "$24": 25,      // Homing feed, mm / min
        "$25": 500,     // Homing seek, mm / min
        "$26": 25,      // Homing debounce, milliseconds
        "$27": 1,       // Homing pull - off, mm
        "$30": 1000,    // Max spindle speed, RPM
        "$31": 0,       // Min spindle speed, RPM
        "$32": 1,       // Laser mode, boolean
        "$100": 250,    // X steps / mm
        "$101": 250,    // Y steps / mm  TODO VARIES
        "$102": 250,    // Z steps / mm
        "$110": 500,    // X Max rate, mm / min
        "$111": 500,    // Y Max rate, mm / min  TODO VARIES
        "$112": 500,    // Z Max rate, mm / min
        "$120": 10,     // X Acceleration, mm / sec ^ 2
        "$121": 10,     // Y Acceleration, mm / sec ^ 2
        "$122": 10,     // Z Acceleration, mm / sec ^ 2
        "$130": 200,    // X Max travel, mm  TODO VARIES
        "$131": 200,    // Y Max travel, mm  TODO VARIES
        "$132": 200  // Z Max travel, mm
    }

    default_value = defaults[input_id.split("_")[1]]
    element = document.getElementById(input_id)
    element.value = default_value
    check_changed(element)
}

// Settings menu scroller
document.getElementById("machine_settings").addEventListener("scroll", evt => {
    var quickLinks = document.querySelectorAll(".menu-list a");
    y_pos = evt.target.scrollTop;

    item_movement = document.getElementById("settings_movement")
    item_controller = document.getElementById("settings_controller")
    item_defaults = document.getElementById("settings_defaults")
    item_connection = document.getElementById("settings_connection")

    if (y_pos > item_movement.offsetTop) {
        // Movement Settings
        quickLinks[0].classList.remove("is-active")
        quickLinks[1].classList.remove("is-active")
        quickLinks[2].classList.remove("is-active")
        quickLinks[3].classList.add("is-active")

    } else if (y_pos > item_controller.offsetTop) {
        // Controller Settings
        quickLinks[0].classList.remove("is-active")
        quickLinks[1].classList.remove("is-active")
        quickLinks[2].classList.add("is-active")
        quickLinks[3].classList.remove("is-active")

    } else if (y_pos > item_defaults.offsetTop) {
        // Default Settings
        quickLinks[0].classList.remove("is-active")
        quickLinks[1].classList.add("is-active")
        quickLinks[2].classList.remove("is-active")
        quickLinks[3].classList.remove("is-active")

    } else {
        // Printer Connection
        quickLinks[0].classList.add("is-active")
        quickLinks[1].classList.remove("is-active")
        quickLinks[2].classList.remove("is-active")
        quickLinks[3].classList.remove("is-active")
    }



}
)

function modal_animation() {
    lottie.loadAnimation({
        container: document.getElementById("animation_check_mode"), // the dom element that will contain the animation
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'branding/animation_check_mode.json' // the path to the animation json
    });
}

// window.addEventListener("scroll", function () {

//     defaults = document.getElementById("settings_defaults")

//     if (window.scrollY > (elementTarget.offsetTop + elementTarget.offsetHeight)) {
//         alert("You've scrolled past the second div");
//     }

//     console.log(windows.scrollY)
// });