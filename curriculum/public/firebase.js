import { initializeApp } from "https://www.gstatic.com/firebasejs/9.0.0/firebase-app.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/9.0.0/firebase-database.js";


const firebaseConfig = {
  apiKey: "AIzaSyADdLAsgmpIdNg5TEE-qE52bSZA49si1Zg",
  authDomain: "line-school-info.firebaseapp.com",
  databaseURL: "https://line-school-info-default-rtdb.firebaseio.com",
  projectId: "line-school-info",
  storageBucket: "line-school-info.appspot.com",
  messagingSenderId: "545093169390",
  appId: "1:545093169390:web:545ae8f69b28f650e043ff",
  measurementId: "G-CK2QDX1Q31"
};

const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

export { database };