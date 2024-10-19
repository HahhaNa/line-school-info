// app.js
import { database } from "./firebase.js"; 
import { ref, set } from "https://www.gstatic.com/firebasejs/9.0.0/firebase-database.js";

const form = document.getElementById("timetableForm");

const urlParams = new URLSearchParams(window.location.search);
const userId = urlParams.get('userId');

form.addEventListener("submit", (event) => {
    event.preventDefault();

    const timetable = {
        monday: [],
        tuesday: [],
        wednesday: [],
        thursday: [],
        friday: []
    };

    const periods = 8; 
    for (let i = 1; i <= periods; i++) {
        console.log("第幾節:", i);

        const mondayClass = form[`monday-${i}`].value.trim();
        const tuesdayClass = form[`tuesday-${i}`].value.trim();
        const wednesdayClass = form[`wednesday-${i}`].value.trim();
        const thursdayClass = form[`thursday-${i}`].value.trim();
        const fridayClass = form[`friday-${i}`].value.trim();

        console.log("Monday:")
        console.log(mondayClass)

        console.log("Tuesday:")
        console.log(tuesdayClass)

        console.log("Wednesday:")
        console.log(wednesdayClass)        

        console.log("Thursday:")
        console.log(thursdayClass)

        console.log("Friday:")
        console.log(fridayClass)        

        // 如果有課程名稱，則記錄下這一節

        if (mondayClass) timetable.monday.push({ period: i, course: mondayClass });
        if (tuesdayClass) timetable.tuesday.push({ period: i, course: tuesdayClass });
        if (wednesdayClass) timetable.wednesday.push({ period: i, course: wednesdayClass });
        if (thursdayClass) timetable.thursday.push({ period: i, course: thursdayClass });
        if (fridayClass) timetable.friday.push({ period: i, course: fridayClass });
    }

    const userRef = ref(database, `timetables/${userId}`);
    set(userRef, timetable)
        .then(() => {
            console.log("課表已成功儲存！");
        })
        .catch((error) => {
            console.error("儲存課表時發生錯誤:", error);
        });
});