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

function set_default(input_id) {
    default_value = defaults[input_id.split("_")[1]]
    element = document.getElementById(input_id)
    element.value = default_value
    check_changed(element)
}

function check_changed(element) {
    id = element.id.split("_")[1]

    old_value = settings_table[id]
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

function toggle_advanced_settings() {
    checked = document.getElementById("switch_advanced_settings").checked
    advanced = document.getElementById("settings_column").querySelectorAll(".advanced_setting");

    for (var i = 0; i < advanced.length; i++) {
        advanced[i].disabled = !checked
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