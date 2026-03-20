// Horizontal Nav css
const navBar = $(".main-nav");
const size = "500px";
const leftsideLimit = -500;

let navbarSize;
let containerWidth;
let maxNavbarLimit;

function setUpHorizontalHeader(){
    navbarSize = navBar.width();
    containerWidth = $(".simplebar-content").width();
    maxNavbarLimit = -(navbarSize - containerWidth);

    if ($("nav").hasClass("horizontal-sidebar")) {
        $(".menu-next").removeClass("d-none");
        $(".menu-previous").removeClass("d-none");
    } else {
        $(".menu-next").addClass("d-none");
        $(".menu-previous").addClass("d-none");
    }
}

$(document).on('click', '.menu-previous', function () {
    const currentPosition = parseInt(navBar.css("marginLeft"));

    if (currentPosition < 0) {
        navBar.css("marginLeft", "+=" + size);
        $(".menu-next").removeClass("d-none");
        $(".menu-previous").removeClass("d-none");

        if (currentPosition >= leftsideLimit) {
            $(this).addClass("d-none");
        }
    }
});

$(document).on('click', '.menu-next', function () {
    const currentPosition = parseInt(navBar.css("marginLeft"));

    if (currentPosition >= maxNavbarLimit) {
        $(".menu-next").removeClass("d-none");
        $(".menu-previous").removeClass("d-none");
        navBar.css("marginLeft", "-=" + size);

        if (currentPosition - parseInt(size) <= maxNavbarLimit) {
            $(this).addClass("d-none");
        }
    }
});

$(function() {
    setUpHorizontalHeader();
});
