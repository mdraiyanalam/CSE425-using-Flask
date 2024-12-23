$(document).ready(function () {
    const textArray = ["Welcome to Kids Calculator!", "Learn Visually,", "and Entertainingly"];
    let index = 0;
    let charIndex = 0;

    function type() {
        if (charIndex < textArray[index].length) {
            $("#typed-text").append(textArray[index].charAt(charIndex));
            charIndex++;
            setTimeout(type, 100);
        } else {
            setTimeout(erase, 2000); // Wait before erasing
        }
    }

    function erase() {
        if (charIndex > 0) {
            $("#typed-text").text(textArray[index].substring(0, charIndex - 1));
            charIndex--;
            setTimeout(erase, 50);
        } else {
            index = (index + 1) % textArray.length; // Loop through the array
            setTimeout(type, 500);
        }
    }

    type();
});
