function show_help(which) {
    document.getElementById("modal_check_mode").classList.add('is-active');
}

function hide_help(which) {
    document.getElementById("modal_check_mode").classList.remove('is-active');
}

function show_settings() {
    element = document.getElementById("machine_settings")
    element.classList.remove('animated', 'slideOutRight');
    element.classList.add('animated', 'slideInRight');
    element.classList.remove('is-hidden');
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
    }, 900);
}