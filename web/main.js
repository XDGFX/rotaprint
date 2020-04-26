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

// --- CLASS CONTENT GENERATOR ---
// Used for anything regarding generation of update of *static* HTML content
// Handles storage of static settings. Dynamic variables and content generation go under the communication class.
class CG {
    // Variable loader
    // Load data in async function so it can be awaited
    // This can be called repeatedly, as fetch() uses cache after the initial request
    // Code is cleaned to reduce filesize
    static load_data = async () => {
        var response

        // Load standard HTML setting
        response = await fetch("templates/setting.html", { cache: "reload" })
        var html_settings = await response.text()
        this.html_settings = html_settings
            .replace(/\n/g, "")
            .replace(/<\!--[\w\W]+?-->/g, "")
            .replace(/[ ]{2,}/g, " ")

        // Load advanced HTML setting
        response = await fetch("templates/setting_advanced.html", { cache: "reload" })
        var html_settings_advanced = await response.text()
        this.html_settings_advanced = html_settings_advanced
            .replace(/\n/g, "")
            .replace(/<\!--[\w\W]+?-->/g, "")
            .replace(/[ ]{2,}/g, " ")

        // Load settings heading
        response = await fetch("templates/setting_heading.html")
        var html_settings_heading = await response.text()
        this.html_settings_heading = html_settings_heading
            .replace(/\n/g, "")
            .replace(/<\!--[\w\W]+?-->/g, "")
            .replace(/[ ]{2,}/g, " ")

        // Load modals html
        response = await fetch("content/modals.html", { cache: "reload" })
        var html_modals = await response.text()
        this.html_modals = html_modals
            .replace(/\n/g, "")
            .replace(/<\!--[\w\W]+?-->/g, "")
            .replace(/[ ]{2,}/g, " ")

        // Load and parse settings json
        response = await fetch("content/settings.json", { cache: "reload" })  // TODO remove cache "reload"
        var settings_json = await response.text()
        this.settings_json = JSON.parse(settings_json)

        // Load and parse errors json
        response = await fetch("content/errors.json", { cache: "reload" })  // TODO remove cache "reload"
        var errors_json = await response.text()
        this.errors_json = JSON.parse(errors_json)
    }

    // Generate HTML content on index.html using external templates and content
    static generate_content = async () => {
        // Load saved data into variables
        // Await required so data is loaded synchronously before attempted html generation
        await this.load_data()

        if (page == "index") {
            // Generate settings page
            this.generate_settings()

            // Generate other static content
            this.generate_static_content()
        }

        // Update settings values and settings page
        COM.update_settings()

        // Get current machine status
        COM.get_current_status("FORCE")

        // Initialise log requester
        COM.get_logs("FORCE")
    }

    // Enter html for static pages
    static generate_static_content() {
        // Modals
        var div = document.querySelector("#modals\\_div")
        div.innerHTML = CG.html_modals
    }

    // --- Help Modals ---
    // Show help modal
    static show_help(which) {
        document.getElementById(which).classList.add('is-active');
    }

    // Hide help modal
    static hide_help(which) {
        var id = which.parentElement.id
        document.getElementById(id).classList.remove('is-active');
        setTimeout(function () {
            CG.modal_animation()
        }, 250);
    }

    // Help modal animations
    static modal_animation(which, toggle) {
        switch (toggle) {
            case 'show':
                this.animation_object = lottie.loadAnimation({
                    container: document.getElementById(which), // the dom element that will contain the animation
                    renderer: 'svg',
                    loop: true,
                    autoplay: true,
                    path: 'branding/animation_check_mode.json' // the path to the animation json
                });
                return
            default:
                if (typeof this.animation_object !== "undefined") {
                    this.animation_object.destroy()
                }
                return
        }
    }

    // --- Settings Page ---
    // Generate settings page based on settings json
    static generate_settings() {
        // Initialise variables
        var html_content = {}
        var html_heading = {}

        // Setup content and heading variables
        for (var item of this.settings_json["categories"]) {
            html_content[item] = ""

            html_heading[item] = this.html_settings_heading
                .replace(/{{item}}/g, item)
        }

        // Loop through setttings JSON and create HTML file
        for (var item of this.settings_json["settings"]) {

            var category = item["category"]

            // Select correct template based on advanced setting or not
            var temp_out
            if (item["advanced"]) {
                temp_out = this.html_settings_advanced
            } else {
                temp_out = this.html_settings
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

        var temp_html = ""
        for (item of this.settings_json["categories"]) {
            temp_html = temp_html
                .concat(html_heading[item])
                .concat(html_content[item])
        }

        // Update HMTL on page
        document.querySelector("#settings_template_div").innerHTML = temp_html
    }

    // Show settings page
    static show_settings() {
        var element = document.getElementById("machine_settings")

        element.classList.remove('animated', 'slideOutRight');
        element.classList.add('animated', 'slideInRight');
        element.classList.remove('is-hidden');

        document.getElementById("settings_apply").disabled = true
        document.getElementById("settings_apply").innerHTML = "Apply Settings"

        COM.update_settings()
    }

    // Hide settings page
    static hide_settings(data) {
        // Check if there are unsaved changes
        if ((this.changed != null) && (this.changed.length > 0) && (data != "FORCE")) {
            bulmaToast.toast({
                message: "There are unsaved settings! <a onclick=\"CG.hide_settings('FORCE')\">Close anyway?</a>",
                type: "is-warning",
                position: "bottom-right",
                dismissible: true,
                closeOnClick: false,
                duration: 4000,
                animate: { in: "fadeInRight", out: "fadeOutRight" }
            });
            return
        }

        // Close settings
        var element = document.getElementById("machine_settings")
        element.classList.remove('animated', 'slideInRight');
        element.classList.add('animated', 'slideOutRight');
        setTimeout(() => {
            element.classList.add('is-hidden');

            // Remove changed warning icons on all settings
            this.changed = element.querySelectorAll(".is-warning");

            for (var i = 0; i < this.changed.length; i++) {
                this.changed[i].classList.remove('is-warning')
            }

            // Remove items from changed variable
            this.changed = []

        }, 900);
    }

    // Toggle advanced settings in settings page
    static toggle_advanced_settings() {
        var checked = document.getElementById("switch_advanced_settings").checked
        var advanced = document.getElementById("settings_column").querySelectorAll(".advanced_setting");

        for (var i = 0; i < advanced.length; i++) {
            advanced[i].disabled = !checked
        }

        var field = document.getElementById("advanced_settings_field")
        if (checked) {
            field.classList.remove("has-text-grey-lighter")
            field.classList.add("has-text-danger")
        } else {
            field.classList.add("has-text-grey-lighter")
            field.classList.remove("has-text-danger")
        }
    }

    // Check if the value of a setting has changed from it's currently assigned value
    static check_changed(element) {
        var id = element.id.replace("setting_", "")

        var old_value = String(COM.settings_table[id])
        var current_value = element.value

        if (old_value == current_value) {
            element.classList.remove("is-warning")
        } else {
            element.classList.add("is-warning")
        }

        // Remove changed warning icons on all settings
        this.changed = document.getElementById("machine_settings").querySelectorAll(".is-warning");
        var button = document.getElementById("settings_apply")

        if (this.changed.length > 0) {
            button.disabled = false
            if (this.changed.length > 1) {
                button.innerHTML = "Apply " + this.changed.length + " Settings"
            } else {
                button.innerHTML = "Apply " + this.changed.length + " Setting"
            }
        } else {
            button.disabled = true
            button.innerHTML = "Apply Settings"
        }

    }

    // Set settings value to default
    static set_default(input_id) {
        var default_value = COM.default_settings[input_id.replace("setting_", "")]
        var element = document.getElementById(input_id)
        element.value = default_value
        this.check_changed(element)
    }

    // Initialise listener for scroll event in settings page, update highlighted link
    static scroller() {
        // Settings menu scroller
        document.getElementById("machine_settings").addEventListener("scroll", evt => {
            // Get current scroll position
            var y_pos = evt.target.scrollTop;

            // Add static settings categories to dynamic categories list
            var categories = ["connection", "default"]
                .concat(CG.settings_json["categories"])

            // Iterate over categories
            for (var i = 0; i < categories.length; i++) {
                var element = document.getElementById("settings_".concat(categories[i]))
                var link = document.querySelector("[href='#settings_".concat(categories[i]).concat("']"));

                // If scroll has passed this category heading, make active, and remove active from all preceeding headings
                if (y_pos > element.offsetTop) {
                    if (i > 0) {
                        for (var j = 0; j <= i; j++) {
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
    }
}

// --- CLASS WEBSOCKET ---
// All functions required for communication over websocket.
// No HTML modification, or variable storage in this class.
class WS {
    static async start() {
        // Initialise websocket
        this.ws = new WebSocket("ws://localhost:8765");

        // Function called when websocket first opened
        this.ws.onopen = function (e) {
            console.log("[open] Connection established");

            WS.check_open_elsewhere()

            // Reset log counter for new session
            WS.ws.send(COM.payloader("RLC"))

            // Remove pageloader
            setTimeout(() => {
                document.getElementById("pageloader").classList.remove('is-active');
            }, 1000);

            // Generate page content
            CG.generate_content()

            // Check connection to grbl
            setTimeout(() => {
                COM.check_connected()
            }, 3000);
        };

        // Function called when message received by websocket
        this.ws.onmessage = function (event) {
            // Separate command and payload from JSON string
            var data = JSON.parse(event.data)
            var command = data["command"]
            var payload = data["payload"]

            // Display message in console if not log or gcs request
            if ((command != "LOG") && (command != "GCS")) {
                console.log(`[message] Data received from server: ${event.data}`);
            }

            // Display error if response contains error
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

            // Command handler
            switch (command) {
                case "GCD":
                    COM.send_gcode(payload);
                    break
                case "FTS":
                    COM.update_settings(payload);
                    break
                case "RQV":
                    // Separate variable and response from payload
                    payload = JSON.parse(payload)
                    var variable = payload["command"]
                    var value = payload["payload"]

                    // Send response based on variable requested
                    switch (variable) {
                        case "grbl":
                            COM.check_connected(value);
                            break
                        case "websocket":
                            WS.check_open_elsewhere(value);
                            break
                    }
                    break
                case "DBS":
                    COM.send_new_settings(payload);
                    break
                case "LOG":
                    COM.get_logs(payload);
                    break
                case "PRN":
                    COM.print_now(payload);
                    break
                case "SET":
                    COM.print_now(payload);
                    break
                case "GCS":
                    COM.get_current_status(payload);
                    break
                case "HME":
                    COM.home(payload);
                    break
                case "FHD":
                    COM.feed_hold(payload);
                    break
                case "FRL":
                    COM.feed_release(payload);
                    break
            }
        };

        // Function called when websocket is closed
        this.ws.onclose = function (event) {
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

        // Function called when there is an error on the websocket
        this.ws.onerror = function (error) {
            // Update pageloader
            document.getElementById("pageloader_title").innerHTML = "An error occured while attempting to connect."
            document.getElementById("pageloader").classList.add('is-stopped');

            // Log error message
            console.log(`[error] ${error.message}`);
        };

        bulmaQuickview.attach();
    }

    // Checks if another websocket connection is already open
    static check_open_elsewhere(data) {
        data = parseInt(data)
        if (data <= 1) {
            console.log("Didn't find any other connections")
            return
        } else if (data > 1) {
            // Redirect to access denied error page
            window.location.replace("access_denied.html");
            return
        }

        console.log("Checking if GUI is open elsewhere...")
        WS.ws.send(COM.payloader("RQV", "websocket"))
    }
}

// --- CLASS COMMUNICATION ---
// Used for communication between frontend and backend.
// Updates content dynamically based on communication.
// Dynamic variables are stored here.
class COM {
    // --- General Functions ---

    // Combine command and payload into JSON string
    static payloader(command, payload) {
        var data = {
            "command": String(command),
            "payload": String(payload)
        }

        data = JSON.stringify(data)
        return data
    }

    static update_surface_speed() {
        var display = document.querySelector("#display\_surface\_speed")
        var radius = document.querySelector("#input_radius").value

        var max_rate_x = COM.settings_table["$110"]
        var max_rate_y = COM.settings_table["$111"]
        var warning_percentage = COM.settings_table["warning_percentage"]

        // mm/min = °/min * (2πr / 360)
        var speed = max_rate_y * (2 * Math.PI * radius / 360)

        // Round to 4dp (function toFixed didn't always work for me)
        speed = Math.round(speed * 1000) / 1000

        display.value = speed.toString().concat(" mm/min")

        var lower_quartile = (100 - warning_percentage) / 100 * max_rate_x
        var upper_quartile = (100 + warning_percentage) / 100 * max_rate_x

        if (speed < lower_quartile || speed > upper_quartile) {
            display.classList.add('is-danger');
            display.classList.remove('is-success');
        } else {
            display.classList.remove('is-danger');
            display.classList.add('is-success');
        }
    }

    // --- Direct Communication ---

    // Send custom message to backend
    static send_custom_code(e, data) {
        if (e.keyCode == 13 || e == "FORCE") {
            var ids = ["manual_command", "manual_payload"]
            var data = []
            var element

            for (var item of ids) {
                element = document.getElementById(item)
                data.push(element.value)
                element.value = ""
            }

            data = this.payloader(data[0], data[1])
            console.log(data)
            WS.ws.send(data)
        } else if (e == "GRB") {
            data = this.payloader("GRB", data)
            WS.ws.send(data)
        }
    }

    // Get settings from database and update form values
    static update_settings(data) {
        // Send command
        if (data == null) {
            WS.ws.send(COM.payloader("FTS"))
            return
        }

        // Split current and default settings
        data = data.split("~<>~")

        // Get settings from response
        this.settings_table = JSON.parse(data[0])

        if (page == "index") {
            var container
            var id

            // Find machine settings, update with current values
            container = document.getElementById("settings_column")
            for (const key of Object.keys(this.settings_table)) {
                id = container.querySelector("#setting_"
                    .concat(key)
                    .replace(/\$/g, "\\$")
                    .replace(/_/g, "\\_")
                )
                if (id != null) {
                    id.value = this.settings_table[key]
                }
            }

            // Update homepage settings with current defaults
            container = document.getElementById("primary_settings_column")
            for (const key of Object.keys(this.settings_table)) {
                id = container.querySelector("#input_"
                    .concat(key)
                    .replace(/\$/g, "\\$")
                    .replace(/_/g, "\\_")
                )
                if (id != null) {
                    // Check if this is a fresh session, only update if true
                    if (this.default_settings == null) {
                        id.value = this.settings_table[key]
                    }
                }
            }

            // Update current print speed based on new settings
            COM.update_surface_speed()
        }

        // Update default settings once only
        if (this.default_settings == null) {
            this.default_settings = JSON.parse(data[1])
        }
    }

    // Send changed settings on settings page to backend
    static send_new_settings(data) {
        switch (data) {
            // On first save, presents confirmation screen
            case "CHECK":
                this.commit_settings = {};
                var html = ""
                var invalid_data = false

                // Generate confirmation table
                for (var i = 0; i < CG.changed.length; i++) {
                    var name = CG.changed[i].id.replace("setting_", "")
                    var new_value = CG.changed[i].value
                    this.commit_settings[name] = new_value

                    // Check for invalid data
                    if (new_value == "") {
                        new_value = "INVALID"
                        invalid_data = true
                    }

                    html = html.concat("<tr><th>", name, "</th><td><code>", COM.settings_table[name], "</code></td><td><code>", new_value, "</code></td></tr>")
                }

                // Update table and show modal
                var tb = document.getElementById("updated_settings_table")
                tb.innerHTML = html
                CG.show_help("modal_confirm_settings")

                // Generate confirm button based on whether there is invalid data
                var confirm_button = document.getElementById("confirm_settings_button")
                if (!invalid_data) {
                    confirm_button.disabled = false
                    confirm_button.innerHTML = "Save changes"
                } else {
                    confirm_button.disabled = true
                    confirm_button.innerHTML = "Invalid Data"
                }
                return

            // Once user clicks confirm on confirmation modal
            case "CONFIRM":
                var send_data = JSON.stringify(this.commit_settings)
                WS.ws.send(COM.payloader("DBS", send_data))
                return

            // Once backend responds that new settings have been received successfully
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
                COM.update_settings()
                return

            // If there was an issue with updating the database
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

    // Get GCODE string when file is uploaded
    // Not technically communication, but linked with send_gcode
    static get_gcode() {
        this.fileInput = document.getElementById('gcode_uploader')
        this.fileInput.onchange = () => {
            if (this.fileInput.files.length > 0) {
                this.send_gcode(this.fileInput)
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
    }

    // Read file selected and send to backend, provide success response if received
    static send_gcode(data) {
        if (data == "DONE") {
            // Update filename
            var fileName = this.fileInput.parentElement.querySelectorAll("p")[0]
            fileName.classList.remove('has-text-grey-lighter');
            fileName.textContent = this.fileInput.files[0].name;

            document.querySelector("#button_print").disabled = false

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

        // Read uploaded file as UTF-8, convert to string and send as payload to backend
        var reader = new FileReader();
        reader.readAsText(this.fileInput.files[0], "UTF-8");
        reader.onload = function (evt) {
            var gcode = evt.target.result;
            WS.ws.send(COM.payloader("GCD", gcode))
        }
    }

    static get_current_status(data) {
        if (data == "FORCE") {
            WS.ws.send(COM.payloader("GCS"))
        } else {
            var current_status = JSON.parse(data)

            // Redirect to correct page based on current status
            if ((page != "monitor") && (current_status["grbl_operation"] != "Idle" && current_status["grbl_operation"] != "Done")) {
                window.location.replace("monitor.html");
                return
            } else if ((page == "monitor") && (current_status["grbl_operation"] == "Idle" || current_status["grbl_operation"] == "Done")) {
                window.location.replace("index.html");
                return
            }

            // Exit here if not on monitor page
            if (page != "monitor") {
                return
            }

            // Update alarm field
            var div = document.getElementById("status_alarm")
            if (current_status["grbl_operation"] == "Alarm") {
                div.classList.remove("is-success")
                div.classList.add("is-danger")
            } else {
                div.classList.add("is-success")
                div.classList.remove("is-danger")
            }

            // Enable 'Complete' button of run is finished
            if (current_status["grbl_operation"] == "Done") {
                document.getElementById("button_complete").disabled = false
            }

            // Update status indicator colour based on current operation
            if (current_status["grbl_operation"].includes("Hold")) {
                document.getElementById("status_grbl").classList.remove("is-success")
                document.getElementById("status_grbl").classList.add("is-warning")
            } else if (current_status["grbl_operation"] == "Run" || current_status["grbl_operation"] == "Done") {
                document.getElementById("status_grbl").classList.add("is-success")
                document.getElementById("status_grbl").classList.remove("is-warning")
            } else {
                document.getElementById("status_grbl").classList.remove("is-success")
                document.getElementById("status_grbl").classList.remove("is-warning")
            }

            var id
            var key

            var container = document.getElementById("monitor_column")
            for (key of Object.keys(current_status)) {
                // Update all matching display elements
                id = container.querySelector("#display_"
                    .concat(key)
                    .replace(/_/g, "\\_")
                )

                if (id != null) {
                    if (id.innerHTML != current_status[key]) {
                        id.innerHTML = current_status[key]
                    }
                    continue
                }

                // Update all matching value elements
                if (id == null) {
                    id = container.querySelector("#value_"
                        .concat(key)
                        .replace(/_/g, "\\_")
                    )
                }

                if ((id != null) && (id.value != current_status[key])) {
                    id.value = current_status[key]
                }
            }

            setTimeout(function () {
                COM.get_current_status("FORCE")
            }, COM.settings_table["polling_interval"]);
        }
    }

    // Get current settings and send the backend, then request print to begin
    static print_now(data) {
        if (data == "DONE") {
            WS.ws.close()
            window.location.replace("monitor.html");
            return
        }

        // Get current print settings
        var div = document.querySelector("#primary\_settings\_column")

        var check_mode = div.querySelector("#switch_check_mode").checked
        var radius = div.querySelector("#input_radius").value
        var length = div.querySelector("#input_length").value
        var batch = div.querySelector("#input_batch").value

        var position_coarse = document.getElementById("input_batch_coarse").value
        var position_fine = document.getElementById("input_batch_fine").value
        var offset = Number(position_coarse) + Number(position_fine)

        data = JSON.stringify(
            {
                "check_mode": check_mode,
                "radius": radius,
                "length": length,
                "batch": batch,
                "offset": offset
            }
        )

        // Send current print settings
        WS.ws.send(COM.payloader("SET", data))

        // Print
        WS.ws.send(COM.payloader("PRN"))
    }

    // --- GRBL communication ---

    // Check if grbl is connected to backend
    static check_connected(data) {
        if (data == "False") {
            // Send notification error
            bulmaToast.toast({
                message: "Could not connect to printer... <a onclick=\"COM.reconnect_printer()\">Retry?</a>",
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

        // If no data, ask backend if grbl is connected
        console.log("Checking printer connection...")
        WS.ws.send(COM.payloader("RQV", "grbl"))
    }

    // Request that backend reconnects to printer
    static reconnect_printer() {
        // Send request
        WS.ws.send(COM.payloader("RCN"))

        // Wait 1s before checking if connection is established
        setTimeout(() => {
            this.check_connected();
        }, 1000);
    }

    // --- Logs and Responses ---

    // Get logs from backend and save to logs_array
    static get_logs(data) {
        if (data == "FORCE") {
            WS.ws.send(COM.payloader("LOG"))
        } else {
            // If initial run
            if (this.logs_array == null) {
                this.logs_array = []

                // Update logs div
                this.force_scroll = true
                COM.update_logs()
            }

            data = data.split("<*>")

            // Check data for specific errors
            for (var i = 0; i < data.length; i += 1) {
                var message = data[i]

                // Grbl error message
                if (message.match(/error:\d{1,2}/)) {
                    // Send warning of an error
                    // bulmaToast.toast({
                    //     message: "An error occured with the firmware. There is a possibility this error can be ignored.\nCheck logs for more details.",
                    //     type: "is-warning",
                    //     position: "bottom-right",
                    //     dismissible: true,
                    //     closeOnClick: false,
                    //     duration: 4000,
                    //     animate: { in: "fadeInRight", out: "fadeOutRight" }
                    // });

                    if (page == "monitor") {
                        var id = message.match(/error:(\d{1,2})/)[1]
                        document.getElementById("status_latest_error").innerHTML = id.concat(" - ", CG.errors_json[Number(id) - 1])
                    }
                }

                // Grbl alarm message
                if (message.match(/ALARM:\d{1,2}/)) {
                    // Send warning of an error
                    bulmaToast.toast({
                        message: "The firmware is reporting an alarm! Check logs for details",
                        type: "is-danger",
                        position: "bottom-right",
                        dismissible: true,
                        closeOnClick: false,
                        duration: 99999999,
                        animate: { in: "fadeInRight", out: "fadeOutRight" }
                    });
                }
            }

            this.logs_array = this.logs_array.concat(data)

            setTimeout(function () {
                COM.get_logs("FORCE")
            }, COM.settings_table["polling_interval"]);
        }
    }

    // Update logs on frontend if required
    static update_logs() {
        // Create log_length variable if required
        if (this.log_length == null) {
            this.log_length = 0
        }

        // Check if logs should be updated
        var update = (!(page == "index") || document.getElementById("logs_auto_update").checked)
        if (!update) {
            setTimeout(function () {
                COM.update_logs()
            }, 1000);
            return
        }

        var elm = document.getElementById("logs_div")
        var scroller = elm.parentElement;

        // Collect all logs up to this point
        var data = this.logs_array.slice(this.log_length)

        // Update log messages length
        this.log_length = this.logs_array.length

        if (elm.innerHTML == "") {
            var table = "<table class=\"table log_table is-family-code\" style=\"width: 100%;\"><tbody>"
        } else {
            var table = elm.innerHTML.slice(0, elm.innerHTML.length - 16)

            // Trim logs to max history length
            var table_elements = table.match(/(<tr[\w\W]+?<\/tr>)/g)

            if (table_elements != null) {
                while (table_elements.length > COM.settings_table["log_history"]) {
                    table_elements.shift()
                }

                table_elements = table_elements.join('')
            } else {
                table_elements = ""
            }
            table = "<table class=\"table log_table is-family-code\" style=\"width: 100%;\"><tbody>".concat(table_elements)

        }

        for (var i = 0; i < data.length; i += 1) {
            // Check that data is an actual log message
            if (data[i] == null || data[i] == "") {
                continue
            }
            // Split data into TIME, TYPE, MESSAGE
            var current_data = data[i].split("<~>")

            // Custom highlight
            var hl = " class=\""

            switch (current_data[1]) {
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

            table = table + "<tr" + hl + "><td>" + current_data[0] + "</td><td>" + current_data[1] + "</td><td>" + current_data[2] + "</td></tr>";
        }

        table = table + "</tbody></table>";

        // Check if logs need to be scrolled
        if ((scroller.scrollHeight - scroller.clientHeight < scroller.scrollTop + 50) || (this.force_scroll == null) || this.force_scroll) {
            var scroll = true
        } else {
            var scroll = false
        }

        // Update html
        elm.innerHTML = table

        // Scroll if needed
        if (scroll) {
            scroller.scrollTop = scroller.scrollHeight;
            this.force_scroll = false
        }

        // Request new update if auto-update enabled
        if (page == "index" && !document.getElementById("logs_quickview").classList.contains("is-active")) {
            this.force_scroll = true
        }

        setTimeout(function () {
            COM.update_logs()
        }, 1000);
    }

    // Rotate part for alignment
    static rotate_y() {
        var position_coarse = document.getElementById("input_batch_coarse").value
        var position_fine = document.getElementById("input_batch_fine").value
        var position = Number(position_coarse) + Number(position_fine)
        WS.ws.send(COM.payloader("GRB", "G0Y".concat(position)))
    }

    // Request homing sequence
    static home(data) {
        // Send command
        if (data == null) {
            WS.ws.send(COM.payloader("HME"))
            return
        }

        if (data == "DONE") {
            // Send notification success
            bulmaToast.toast({
                message: "Requested homing cycle!",
                type: "is-success",
                position: "bottom-right",
                dismissible: true,
                closeOnClick: false,
                duration: 4000,
                animate: { in: "fadeInRight", out: "fadeOutRight" }
            });
        }

    }

    static feed_hold(data) {
        // Send command
        if (data == null) {
            WS.ws.send(COM.payloader("FHD"))
            return
        }

        if (data == "DONE") {
            // Send notification success
            bulmaToast.toast({
                message: "Feed hold received",
                type: "is-success",
                position: "bottom-right",
                dismissible: true,
                closeOnClick: false,
                duration: 4000,
                animate: { in: "fadeInRight", out: "fadeOutRight" }
            });
        }
    }

    static feed_release(data) {
        // Send command
        if (data == null) {
            WS.ws.send(COM.payloader("FRL"))
            return
        }

        if (data == "DONE") {
            // Send notification success
            bulmaToast.toast({
                message: "Continue request received",
                type: "is-success",
                position: "bottom-right",
                dismissible: true,
                closeOnClick: false,
                duration: 4000,
                animate: { in: "fadeInRight", out: "fadeOutRight" }
            });
        }
    }
}

// Setup event handlers
WS.start()

if (page == "index") {
    COM.get_gcode()
    CG.scroller()
}
