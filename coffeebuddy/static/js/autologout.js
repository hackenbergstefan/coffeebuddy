function startAutologout(autologoutTime = 5,
                         containerSelector = "#autologout-bar-container",
                         logoutElementClass = "autologout-bar-ruler",
                         elementCount = 20)
{
    setTimeout(() => {
        window.location.href = '../';
    }, autologoutTime * 1000);
    setInterval(() => {
        $(containerSelector).children()[0].remove();
    }, autologoutTime / elementCount * 1000);
    for (var i = 0; i < elementCount; i++) {
        $("<div></div>")
            .appendTo(containerSelector)
            .addClass(logoutElementClass)
            .css('margin-right',
                 $(containerSelector).width() / elementCount -
                 $("." + logoutElementClass).first().width());
    }
}
