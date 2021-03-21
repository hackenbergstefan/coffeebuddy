/* inspired by Boujjou Achraf's matrix: https://codepen.io/wefiy/pen/WPpEwo */

/* get canvas */
var canvas = document.getElementById("matrix");
var ctx = canvas.getContext("2d");

/* canvas to full screen */
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

var matrix_text_color = "#ff5b91";
var matrix_fg_color = getComputedStyle(document.body).getPropertyValue('--color-engineering');

var chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%+-/~{[|`]}タダチヂッツヅテデトドナニヌネノハ".split("");
var font_size = 10;
var columns = canvas.width / font_size;  /* number of character columns */
var drops = [];  /* y-coordinates of the drops, one drop per column */

async function sha256(message) {
    /* encode as UTF-8 */
    const msgBuffer = new TextEncoder().encode(message);

    /* hash the message */
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);

    /* convert ArrayBuffer to Array */
    const hashArray = Array.from(new Uint8Array(hashBuffer));

    /* convert bytes to hex string */
    const hashHex = hashArray.map(b => ('00' + b.toString(16)).slice(-2)).join('');
    return hashHex;
}

function coffee_prepare() {
    /* text color to white */
    var all = document.getElementsByTagName("*");
    for (var i=0, max=all.length; i < max; i++) {
        all[i].style.color = matrix_fg_color;
    }
    document.getElementById("coffeemeter-bar").style.background = matrix_fg_color;

    /* replace fontawesome coffee icon */
    document.getElementById("btn-coffee-icon").classList.remove('fa-coffee');
    document.getElementById("btn-coffee-icon").classList.add('fa-user-secret');

    /* replace coffee text */
    document.getElementById("btn-coffee-text").textContent = "T4k3 a c4f3";
    canvas.style.visibility = "visible";

}

function matrix_prepare() {
    /* canvas background to black */
    // ctx.fillStyle = "rgba(0, 0, 0)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    /* all drops are y=1 at start */
    for(var x = 0; x < columns; x++) {
        /* sweep effect at the beginning */
        drops[x] = 1;
        // drops[x] = -Math.floor(Math.random()*canvas.height/10);
    }
}

function matrix_draw() {
    /* black background, translucent to show trails */
    ctx.fillStyle = "rgba(0, 0, 0, 0.04)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    /* text style */
    ctx.fillStyle = matrix_text_color;
    ctx.font = font_size + "px arial";

    /* for every drop column */
    for(var i = 0; i < drops.length; i++) {
        /* select random character */
        var text = chars[Math.floor(Math.random()*chars.length)];

        /* draw character */
        var x = i * font_size;
        var y = drops[i] * font_size;
        ctx.fillText(text, x, y);

        /* send drop back to top (with added randomness for scattering) */
        if(y > canvas.height && Math.random() > 0.975)
            drops[i] = 0;

        /* have drop fall by one */
        drops[i]++;
    }
}

function matrix_start() {
    coffee_prepare();
    matrix_prepare();
    setInterval(matrix_draw, 35);
}

var salt = "59ecf0380ab60a048aa5f9536e1642aa5de99371cbf903a383d5afa51f580ef7"
var user = document.getElementById("user-name").textContent
var magic_user_hashes = [
    "81eabd2b8f3c1558706bd325f5e15da13d78f73ce4f1914a6b41d9572eccbe0d",
]

/* run matrix if salted user name in list of magic hashes */
sha256(salt + user).then(function(digest) {
    if (magic_user_hashes.indexOf(digest) > -1) {
        matrix_start();
    }
});

/* or just if you like */
if (window.location.search.search('matrix') > -1)
{
    matrix_start();
}
