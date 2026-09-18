// ================================
// PSF PLAFITNESS JAVASCRIPT
// ================================


// ================================
// MOBILE MENU
// ================================

const menuButton = document.getElementById("menuButton");
const navLinks = document.querySelector(".nav-links");

if (menuButton && navLinks) {

    menuButton.addEventListener("click", function () {

        navLinks.classList.toggle("mobile-active");

    });

}


// ================================
// BOOKING CALENDAR
// ================================

const bookingForm = document.getElementById("bookingForm");

const calendarDays = document.getElementById("calendarDays");

const calendarMonth = document.getElementById("calendarMonth");

const previousMonth = document.getElementById("previousMonth");

const nextMonth = document.getElementById("nextMonth");

const selectedDateText = document.getElementById("selectedDateText");

const dateInput = document.getElementById("date");

const timeInput = document.getElementById("time");

const timeSlots = document.getElementById("timeSlots");

const bookingMessage = document.getElementById("bookingMessage");


// 9 AM through 4 PM
// Each appointment is 60 minutes.

const availableTimes = [
    "09:00 AM",
    "10:00 AM",
    "11:00 AM",
    "12:00 PM",
    "01:00 PM",
    "02:00 PM",
    "03:00 PM",
    "04:00 PM"
];


let currentCalendarDate = new Date();

let selectedDate = null;


// ================================
// GET TODAY
// ================================

function getToday() {

    const today = new Date();

    today.setHours(0, 0, 0, 0);

    return today;

}


// ================================
// FORMAT DATE
// ================================

function formatDate(date) {

    const year = date.getFullYear();

    const month = String(
        date.getMonth() + 1
    ).padStart(2, "0");

    const day = String(
        date.getDate()
    ).padStart(2, "0");

    return `${year}-${month}-${day}`;

}


// ================================
// DISPLAY CALENDAR
// ================================

function renderCalendar() {

    if (!calendarDays || !calendarMonth) {
        return;
    }


    calendarDays.innerHTML = "";


    const year =
        currentCalendarDate.getFullYear();

    const month =
        currentCalendarDate.getMonth();


    const monthName =
        currentCalendarDate.toLocaleString(
            "default",
            {
                month: "long"
            }
        );


    calendarMonth.textContent =
        `${monthName} ${year}`;


    const firstDay =
        new Date(year, month, 1).getDay();


    const daysInMonth =
        new Date(year, month + 1, 0).getDate();


    const today = getToday();


    // Empty spaces before first day

    for (let i = 0; i < firstDay; i++) {

        const emptyDay =
            document.createElement("div");

        emptyDay.classList.add(
            "calendar-empty"
        );

        calendarDays.appendChild(emptyDay);

    }


    // Create each day

    for (let day = 1; day <= daysInMonth; day++) {

        const button =
            document.createElement("button");


        button.type = "button";

        button.textContent = day;

        button.classList.add(
            "calendar-day"
        );


        const thisDate =
            new Date(year, month, day);

        thisDate.setHours(0, 0, 0, 0);


        const dateString =
            formatDate(thisDate);


        // Disable dates in the past

        if (thisDate < today) {

            button.disabled = true;

            button.classList.add(
                "past-date"
            );

        }


        // Highlight today

        if (
            thisDate.getTime() ===
            today.getTime()
        ) {

            button.classList.add(
                "today-date"
            );

        }


        // Highlight selected date

        if (
            selectedDate === dateString
        ) {

            button.classList.add(
                "selected-date"
            );

        }


        button.addEventListener(
            "click",
            function () {

                selectDate(dateString);

            }
        );


        calendarDays.appendChild(button);

    }

}


// ================================
// SELECT DATE
// ================================

async function selectDate(dateString) {

    selectedDate = dateString;

    dateInput.value = dateString;

    timeInput.value = "";


    const dateObject =
        new Date(
            dateString + "T00:00:00"
        );


    selectedDateText.textContent =
        dateObject.toLocaleDateString(
            "en-US",
            {
                weekday: "long",
                month: "long",
                day: "numeric",
                year: "numeric"
            }
        );


    renderCalendar();


    await loadAvailableTimes(dateString);

}


// ================================
// LOAD AVAILABLE TIMES
// ================================

async function loadAvailableTimes(dateString) {

    timeSlots.innerHTML =
        "<p>Loading available times...</p>";


    try {

        const response =
            await fetch(
                `/booked-times?date=${dateString}`
            );


        const bookedTimes =
            await response.json();


        timeSlots.innerHTML = "";


        availableTimes.forEach(
            function (time) {

                const button =
                    document.createElement("button");


                button.type = "button";

                button.textContent = time;

                button.classList.add(
                    "time-slot"
                );


                if (
                    bookedTimes.includes(time)
                ) {

                    button.disabled = true;

                    button.classList.add(
                        "time-unavailable"
                    );

                    button.textContent =
                        `${time} • Booked`;

                }


                button.addEventListener(
                    "click",
                    function () {

                        if (
                            button.disabled
                        ) {
                            return;
                        }


                        document
                            .querySelectorAll(
                                ".time-slot"
                            )
                            .forEach(
                                function (slot) {

                                    slot.classList
                                        .remove(
                                            "selected-time"
                                        );

                                }
                            );


                        button.classList.add(
                            "selected-time"
                        );


                        timeInput.value =
                            time;

                    }
                );


                timeSlots.appendChild(
                    button
                );

            }
        );


    } catch (error) {

        timeSlots.innerHTML =
            "<p>Unable to load available times. Please try again.</p>";

    }

}


// ================================
// MONTH NAVIGATION
// ================================

if (previousMonth) {

    previousMonth.addEventListener(
        "click",
        function () {

            currentCalendarDate.setMonth(
                currentCalendarDate.getMonth() - 1
            );


            const today = getToday();

            const currentMonth =
                new Date(
                    today.getFullYear(),
                    today.getMonth(),
                    1
                );


            if (
                currentCalendarDate <
                currentMonth
            ) {

                currentCalendarDate =
                    currentMonth;

            }


            renderCalendar();

        }
    );

}


if (nextMonth) {

    nextMonth.addEventListener(
        "click",
        function () {

            currentCalendarDate.setMonth(
                currentCalendarDate.getMonth() + 1
            );


            renderCalendar();

        }
    );

}


// ================================
// BOOKING FORM
// ================================

if (bookingForm) {

    bookingForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const name =
                document
                    .getElementById("name")
                    .value
                    .trim();


            const email =
                document
                    .getElementById("email")
                    .value
                    .trim();


            const session =
                document
                    .getElementById("session")
                    .value;


            const date =
                dateInput.value;


            const time =
                timeInput.value;


            // Check information

            if (
                !name ||
                !email ||
                !session
            ) {

                bookingMessage.textContent =
                    "Please fill out all booking information.";

                bookingMessage.className =
                    "form-message error-message";

                return;

            }


            if (!date) {

                bookingMessage.textContent =
                    "Please choose a date.";

                bookingMessage.className =
                    "form-message error-message";

                return;

            }


            if (!time) {

                bookingMessage.textContent =
                    "Please choose an available time.";

                bookingMessage.className =
                    "form-message error-message";

                return;

            }


            try {

                const response =
                    await fetch(
                        "/book",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                name: name,
                                email: email,
                                session: session,
                                date: date,
                                time: time
                            })
                        }
                    );


                const result =
                    await response.json();


                bookingMessage.textContent =
                    result.message;


                if (result.success) {

                    bookingMessage.className =
                        "form-message success-message";


                    bookingForm.reset();


                    selectedDate = null;

                    dateInput.value = "";

                    timeInput.value = "";


                    selectedDateText.textContent =
                        "Please choose a date";


                    timeSlots.innerHTML =
                        '<p class="choose-date-message">Please choose a date first.</p>';


                    renderCalendar();

                } else {

                    bookingMessage.className =
                        "form-message error-message";

                }


            } catch (error) {

                bookingMessage.textContent =
                    "Something went wrong. Please try again.";

                bookingMessage.className =
                    "form-message error-message";

            }

        }
    );

}


// ================================
// CONTACT FORM
// ================================

const contactForm =
    document.getElementById("contactForm");

const contactResponse =
    document.getElementById("contactResponse");


if (contactForm) {

    contactForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const name =
                document
                    .getElementById("contactName")
                    .value
                    .trim();


            const email =
                document
                    .getElementById("contactEmail")
                    .value
                    .trim();


            const message =
                document
                    .getElementById("contactMessage")
                    .value
                    .trim();


            if (
                !name ||
                !email ||
                !message
            ) {

                contactResponse.textContent =
                    "Please fill out all fields.";

                return;

            }


            try {

                const response =
                    await fetch(
                        "/contact",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                name: name,
                                email: email,
                                message: message
                            })
                        }
                    );


                const result =
                    await response.json();


                contactResponse.textContent =
                    result.message;


                if (result.success) {

                    contactForm.reset();

                }


            } catch (error) {

                contactResponse.textContent =
                    "Something went wrong. Please try again.";

            }

        }
    );

}


// ================================
// NAVIGATION ANIMATION
// ================================

window.addEventListener(
    "scroll",
    function () {

        const navbar =
            document.querySelector(".navbar");


        if (!navbar) {
            return;
        }


        if (window.scrollY > 50) {

            navbar.style.background =
                "rgba(1, 5, 10, 0.98)";

        } else {

            navbar.style.background =
                "rgba(1, 5, 10, 0.92)";

        }

    }
);


// ================================
// START CALENDAR
// ================================

renderCalendar();