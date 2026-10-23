function showPage(id){

let pages=document.querySelectorAll(".page");

pages.forEach(p=>p.style.display="none");

document.getElementById(id).style.display="block";

}

showPage("dashboard");

/* trust score animation */

let score=0;

let interval=setInterval(()=>{

if(score>=92){

clearInterval(interval);

}else{

score++;

document.getElementById("score").innerText=score+"%";

}

},30);

/* scan animation */

function startScan(){

let bar=document.getElementById("bar");

let width=0;

let scan=setInterval(()=>{

if(width>=100){

clearInterval(scan);

}else{

width++;

bar.style.width=width+"%";

}

},20);

}

setTimeout(() => {
    window.location.href = "home.html";
}, 3000);