/* 
 * Copyright (c) 2020
 * This file is part of the TDCA rotary printer project.
 * 
 * @summary Scripts used for the front-end GUI for TDCA rotary printer.
 * @author Callum Morrison <callum.morrison@mac.com>, 2020
 * 
 * Unauthorized copying of this file, via any medium is strictly prohibited
 * Proprietary and confidential
 */

// VARIABLE LOADER
// Load data in async function so it can be awaited
// This can be called repeatedly, as fetch() uses cache after the initial request
// Code is cleaned to reduce filesize
load_data = async () => {
    // Load standard HTML setting
    response = await fetch("web/templates/setting.html")
    html_settings = await response.text()
    html_settings = html_settings
        .replace(/\n/g, "")
        .replace(/<\!--[\w\W]+?-->/g, "")
        .replace(/[ ]{2,}/g, " ")

    // Load advanced HTML setting
    response = await fetch("web/templates/setting_advanced.html")
    html_settings_advanced = await response.text()
    html_settings_advanced = html_settings_advanced
        .replace(/\n/g, "")
        .replace(/<\!--[\w\W]+?-->/g, "")
        .replace(/[ ]{2,}/g, " ")

    // Load settings heading
    response = await fetch("web/templates/setting_heading.html")
    html_settings_heading = await response.text()
    html_settings_heading = html_settings_heading
        .replace(/\n/g, "")
        .replace(/<\!--[\w\W]+?-->/g, "")
        .replace(/[ ]{2,}/g, " ")

    // Load modals html
    response = await fetch("web/content/modals.html")
    html_modals = await response.text()
    html_modals = html_modals
        .replace(/\n/g, "")
        .replace(/<\!--[\w\W]+?-->/g, "")
        .replace(/[ ]{2,}/g, " ")

    // Load and parse settings json
    response = await fetch("web/content/settings.json", { cache: "reload" })
    settings_json = await response.text()
    settings_json = JSON.parse(settings_json)

    return [html_settings, html_settings_advanced, settings_json, html_settings_heading, html_modals]
}

// Generate HTML content on index.html using external templates and content
async function generate_content() {
    // Load saved data into variables
    // Await required so data is loaded synchronously before attempted html generation
    await load_data()

    // Generate settings page
    generate_settings()

    // Generate other static content
    generate_static_content()

    // Update settings page
    update_settings()
}

function generate_static_content() {
    div = document.querySelector("#modals\\_div")
    div.innerHTML = html_modals
}

// WEBSOCKET
// Initialise websocket
ws = new WebSocket("ws://localhost:8765");
response = "";

// Function to call when websocket first opened
ws.onopen = function (e) {
    console.log("[open] Connection established");

    // Remove pageloader
    setTimeout(() => {
        document.getElementById("pageloader_title").innerHTML = "Connected!";
    }, 500);

    setTimeout(() => {
        document.getElementById("pageloader").classList.remove('is-active');
    }, 1000);

    // Generate page content
    generate_content()

    // Reset log counter for new session
    ws.send(payloader("RLC"))

    // Check connection to grbl
    setTimeout(() => {
        check_connected()
    }, 3000);
};

// Function to call when message received by websocket
ws.onmessage = function (event) {
    data = JSON.parse(event.data)
    command = data["command"]
    payload = data["payload"]

    if (command == "LOG") {
        console.log(`[message] Data received from server: (log update)`);
    } else {
        console.log(`[message] Data received from server: ${event.data}`);
    }

    if (payload == "ERROR") {
        bulmaToast.toast({
            message: "An error occured with command: ".concat(command).concat("\nCheck logs for more info."),
            type: "is-danger",
            position: "bottom-right",
            dismissible: true,
            closeOnClick: false,
            duration: 99999999,
            animate: { in: "fadeInRight", out: "fadeOutRight" }
        });

        return
    }

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
        case "LOG":
            update_logs(payload);
            break
        case "PRN":
            print_now(payload);
            break
    }
};

// Function to call when websocket is closed
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
    if (e.keyCode == 13 || e == "FORCE") {
        ids = ["manual_command", "manual_payload"]
        data = []

        for (item of ids) {
            element = document.getElementById(item)
            data.push(element.value)
            element.value = ""
        }

        data = payloader(data[0], data[1])
        console.log(data)
        ws.send(data)
    }
}

fileInput = document.getElementById('gcode_uploader')
fileInput.onchange = () => {
    if (fileInput.files.length > 0) {
        send_gcode(fileInput)
    } else {
        bulmaToast.toast({
            message: "No file selected...",
            type: "is-danger",
            position: "bottom-right",
            dismissible: true,
            closeOnClick: false,
            animate: { in: "fadeInRight", out: "fadeOutRight" }
        });
    }
}

function send_gcode(data) {
    // Read file selected and send to backend, provide success response if received
    if (data == "DONE") {

        fileName = fileInput.parentElement.querySelectorAll("p")[0]
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

    var reader = new FileReader();
    reader.readAsText(fileInput.files[0], "UTF-8");
    reader.onload = function (evt) {
        gcode = evt.target.result;
        ws.send(payloader("GCD", gcode))
    }

}

function print_now(data) {
    if (data == "DONE") {
        // Send notification success
        bulmaToast.toast({
            message: "Printing now!",
            type: "is-success",
            position: "bottom-right",
            dismissible: true,
            closeOnClick: false,
            duration: 4000,
            animate: { in: "fadeInRight", out: "fadeOutRight" }
        });

        return
    }

    // Get current print settings
    div = document.querySelector("#primary\_settings\_column")

    check_mode = div.querySelector("#switch_check_mode").value
    radius = div.querySelector("#input_radius").value
    length = div.querySelector("#input_length").value
    batch = div.querySelector("#input_batch").value

    data = JSON.stringify(
        {
            "check_mode": check_mode,
            "radius": radius,
            "length": length,
            "batch": batch,
        }
    )

    // Send current print settings
    ws.send(payloader("SET", data))

    // Print
    ws.send(payloader("PRN"))
}

// DATABASE

// Get settings from database and update form values
// Set default variable to make global
settings_table = ""
default_settings = ""
function update_settings(data) {
    // Send command
    if (data == null) {
        ws.send(payloader("FTS"))
        return
    }

    // Split current and default settings
    data = data.split("~<>~")

    // Get settings from response
    settings_table = JSON.parse(data[0])

    // Find machine settings, update with current values
    container = document.getElementById("settings_column")
    for (const key of Object.keys(settings_table)) {
        id = container.querySelector("#setting_"
            .concat(key)
            .replace(/\$/g, "\\$")
            .replace(/_/g, "\\_")
        )
        if (id != null) {
            id.value = settings_table[key]
        }
    }

    // Update default settings once only
    if (default_settings == "") {
        default_settings = JSON.parse(data[1])
    }

    // Update homepage settings with current defaults
    container = document.getElementById("primary_settings_column")
    for (const key of Object.keys(settings_table)) {
        id = container.querySelector("#input_"
            .concat(key)
            .replace(/\$/g, "\\$")
            .replace(/_/g, "\\_")
        )
        if (id != null) {
            // Only update if new session
            if (id.value == "") {
                id.value = settings_table[key]
            }
        }
    }

    // Update current print speed based on new settings
    update_surface_speed()
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

            // Update new settings to variable
            update_settings()
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
    ws.send(payloader("RQV", "connected"))
}

function reconnect_printer() {
    ws.send(payloader("RCN"))
    setTimeout(() => {
        check_connected();
    }, 1000);
}


// HELP
function show_help(which) {
    document.getElementById(which).classList.add('is-active');
}

function hide_help(which) {
    id = which.parentElement.id
    document.getElementById(id).classList.remove('is-active');
    setTimeout(function () {
        modal_animation()
    }, 250);
}

function update_surface_speed() {
    display = document.querySelector("#display\_surface\_speed")
    radius = document.querySelector("#input_radius").value

    max_rate_x = settings_table["$110"]
    max_rate_y = settings_table["$111"]
    warning_percentage = settings_table["warning_percentage"]

    // mm/min = °/min * (2πr / 360)
    speed = max_rate_y * (2 * Math.PI * radius / 360)

    // mm = ° * (2πr / 360)
    // deg = mm * (360 / 2πr)

    // Round to 4dp (function toFixed didn't always work for me)
    speed = Math.round(speed * 1000) / 1000

    display.value = speed.toString().concat(" mm/min")

    lower_quartile = (100 - warning_percentage) / 100 * max_rate_x
    upper_quartile = (100 + warning_percentage) / 100 * max_rate_x

    if (speed < lower_quartile || speed > upper_quartile) {
        display.classList.add('is-danger');
        display.classList.remove('is-success');
    } else {
        display.classList.remove('is-danger');
        display.classList.add('is-success');
    }
}


// SETTINGS
// Insert settings html into div
async function generate_settings() {
    // Select div to insert content to
    div = document.querySelector("#settings_template_div")

    // Initialise variables
    html_content = {}
    html_heading = {}

    // Setup content and heading variables
    for (item of settings_json["categories"]) {
        html_content[item] = ""

        html_heading[item] = html_settings_heading
            .replace(/{{item}}/g, item)
    }

    // Loop through setttings JSON and create HTML file
    for (item of settings_json["settings"]) {

        category = item["category"]

        // Select correct template based on advanced setting or not
        if (item["advanced"]) {
            temp_out = html_settings_advanced
        } else {
            temp_out = html_settings
        }

        // Replace variables
        temp_out = temp_out
            .replace(/{{title}}/g, item["title"])
            .replace(/{{id}}/g, item["id"])
            .replace(/{{unit}}/g, item["unit"])
            .replace(/{{help}}/g, item["help"])

        // Update main string
        html_content[category] = html_content[category].concat(temp_out)
    }

    temp_html = ""
    for (item of settings_json["categories"]) {
        temp_html = temp_html
            .concat(html_heading[item])
            .concat(html_content[item])
    }

    // Update HMTL on page
    div.innerHTML = temp_html
}

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
    id = element.id.replace("setting_", "")

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
    id = input_id.replace("setting_", "")

    default_value = default_settings[input_id.replace("setting_", "")]
    element = document.getElementById(input_id)
    element.value = default_value
    check_changed(element)
}

// Settings menu scroller
document.getElementById("machine_settings").addEventListener("scroll", evt => {
    // Get current scroll position
    y_pos = evt.target.scrollTop;

    // Add static settings categories to dynamic categories list
    categories = ["connection", "default"]
        .concat(settings_json["categories"])

    // Iterate over categories
    for (i = 0; i < categories.length; i++) {
        element = document.getElementById("settings_".concat(categories[i]))
        link = document.querySelector("[href='#settings_".concat(categories[i]).concat("']"));

        // If scroll has passed this category heading, make active, and remove active from all preceeding headings
        if (y_pos > element.offsetTop) {
            if (i > 0) {
                for (j = 0; j <= i; j++) {
                    link = document.querySelector("[href='#settings_".concat(categories[j]).concat("']"));
                    link.classList.remove("is-active")
                }
            }
            link.classList.add("is-active")
        } else if (i != 0) {
            link.classList.remove("is-active")
        }
    }
})

var animation_object
function modal_animation(which, toggle) {
    switch (toggle) {
        case 'show':
            animation_object = lottie.loadAnimation({
                container: document.getElementById(which), // the dom element that will contain the animation
                renderer: 'svg',
                loop: true,
                autoplay: true,
                path: 'branding/animation_check_mode.json' // the path to the animation json
            });
            return
        default:
            if (typeof animation_object !== "undefined") {
                animation_object.destroy()
            }
            return
    }
}

// LOGS
var quickviews = bulmaQuickview.attach(); // quickviews now contains an array of all Quickview instances
function update_logs(data) {
    update = document.getElementById("logs_auto_update").checked
    if (!update) {
        return
    }

    elm = document.getElementById("logs_div")
    scroller = elm.parentElement;

    if (data == "FORCE") {
        ws.send(payloader("LOG"))
    } else {
        data = data.replace(/(?:\r\n|\r|\n)/g, "<~>")
        data = data.replace(/(<#>)/g, "\n")
        data = data.split("<~>")

        if (elm.innerHTML == "") {
            table = "<table class=\"table log_table is-striped is-family-code\">"
        } else {
            // table = elm.innerHTML
            table = elm.innerHTML.slice(0, elm.innerHTML.length - 8)
        }

        for (var i = 0; i < data.length - 2; i += 3) {
            hl = "class=\""

            switch (data[i + 1]) {
                case "INFO":
                    hl = hl + "has-background-info has-text-white\""
                    break
                case "WARNING":
                    hl = hl + "has-background-warning\""
                    break
                case "ERROR":
                    hl = hl + "has-background-danger has-text-white\""
                    break
                default:
                    hl = ""
                    break
            }

            table = table + "<tr " + hl + "><td>" + data[i] + "</td><td>" + data[i + 1] + "</td><td>" + data[i + 2] + "</td></tr>";
        }

        table = table + "</table>";

        if ((scroller.scrollHeight - scroller.clientHeight < scroller.scrollTop + 50) || force_scroll) {
            scroll = true
        } else {
            scroll = false
        }

        if (elm.innerHTML == "") {
            elm.innerHTML = table
            scroll = true
        } else {
            elm.innerHTML = table
        }

        if (scroll) {
            scroller.scrollTop = scroller.scrollHeight;
            force_scroll = false
        }

        if (document.getElementById("logs_quickview").classList.contains("is-active")) {
            if (update) {
                setTimeout(function () {
                    update_logs("FORCE")
                }, 1000);
            }
        } else {
            force_scroll = true
        }
    }

}