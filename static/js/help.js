function show_help(which) {
    document.getElementById(which).classList.add('is-active');
}

function hide_help(which) {
    id = which.parentElement.id
    document.getElementById(id).classList.remove('is-active');
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