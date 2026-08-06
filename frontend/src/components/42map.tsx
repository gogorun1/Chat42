import { useState } from "react";

import building42 from "../assets/maps/42.svg";
import cantineM1 from "../assets/maps/cantine.svg";
import cantine0 from "../assets/maps/cantine.svg";
import f0 from "../assets/maps/f0.svg";
import f1 from "../assets/maps/f1.svg";
import f2 from "../assets/maps/f2.svg";
import f6 from "../assets/maps/f6.svg";
import play from "../assets/maps/play.svg";
import roof from "../assets/maps/roof.svg";
import stairs from "../assets/maps/stairs.svg";

import cat from "../assets/maps/cat.svg";

import { lastSighting } from "../data/cat";
import { sightings } from "../data/sighting";

import GameMenu from "./GameMenu";
import ReportButton from "./ReportButton";
import GuessCat from "./GuessCat.tsx";


const zones:any = {

    entrance:{
        id:"entrance",
        name:"42 Entrance",
        floor:"Entrance",
        image:building42
    },


    cantine_m1:{
        id:"cantine_m1",
        name:"CantiSkate",
        floor:"-1",
        image:cantineM1
    },


    cantine_0:{
        id:"cantine_0",
        name:"Shokudo",
        floor:"0",
        image:cantine0
    },


    cantine_1:{
        id:"cantine_1",
        name:"La Piscine",
        floor:"0",
        image:cantine0
    },


    f0:{
        id:"f0",
        name:"Floor 0 Room",
        floor:"0",
        image:f0
    },


    f1:{
        id:"f1",
        name:"Floor 1 Room",
        floor:"1",
        image:f1
    },


    f2:{
        id:"f2",
        name:"Floor 2 Room",
        floor:"2",
        image:f2
    },


    f6:{
        id:"f6",
        name:"Floor 6",
        floor:"6",
        image:f6
    },


    playroom:{
        id:"playroom",
        name:"Cafe avant la fin du monde",
        floor:"2",
        image:play
    },


    roof2:{
        id:"roof2",
        name:"Terrase (2)",
        floor:"2",
        image:roof
    },


    roof3:{
        id:"roof3",
        name:"Terrase (3)",
        floor:"3",
        image:roof
    },


    stairs:{
        id:"stairs",
        name:"Stairs",
        floor:"All",
        image:stairs
    }

};






export default function CampusMap(){


const [page,setPage] =
useState("map");


const [selectedZone,setSelectedZone] =
useState(lastSighting.zone);



const currentZone =
zones[selectedZone];





const heat:any = {};



sightings.forEach((s)=>{

    heat[s.zone] =
    (heat[s.zone] || 0)+1;

});







return (

<div
className="
min-h-screen
bg-slate-950
text-white
p-6
pb-32
"
>





{/* ================= HUD ================= */}


<div
className="
flex
justify-between
items-center
bg-slate-900
border
border-yellow-400
rounded-xl
p-4
mb-6
"
>



<div>


<h1
className="
text-3xl
text-yellow-400
font-bold
"
>

🐱 Chat42

</h1>


<p
className="
text-sm
text-slate-400
"
>

Campus Cat Adventure

</p>


</div>





<div
className="
text-right
"
>


<p>

👤 Player

</p>


<p
className="
text-yellow-400
font-bold
"
>

⭐ 120 pts

</p>


<p>

🏆 Rank #12

</p>


</div>


</div>







{/* ================= MAP ================= */}



{
page==="map" &&

<div>


<div
className="
flex
flex-wrap
justify-center
gap-3
mb-6
"
>


{
Object.keys(zones).map((zone)=>(


<button

key={zone}

onClick={()=>
setSelectedZone(zone)
}

className="
border
border-yellow-400
bg-slate-800
px-3
py-2
rounded
hover:bg-yellow-600
"

>

{zones[zone].name}

</button>


))

}


</div>






<div
className="
relative
flex
justify-center
"
>


<img

src={currentZone.image}

className="map-svg"

/>



{
selectedZone===lastSighting.zone &&

<>


<div
className="cat-glow"
/>


<img

src={cat}

className="cat-icon"

/>


</>

}



</div>








<div
className="
mt-6
bg-slate-900
border
border-yellow-400
rounded-xl
p-5
"
>


<h2
className="
text-xl
text-yellow-400
"
>

📍 Last Seen

</h2>


<p>
Zone: {lastSighting.zone}
</p>


<p>
Reporter: {lastSighting.reporter}
</p>


<p>
Time: {lastSighting.time}
</p>



</div>



</div>

}









{/* ================= HISTORY ================= */}



{
page==="history" &&


<div>


<h2 className="text-2xl mb-5">

🐾 Cat History

</h2>



{
sightings.map((s,index)=>(


<div

key={index}

className="
bg-slate-900
rounded-xl
p-4
mb-3
"

>


🐾 {s.zone}

<br/>

👤 {s.reporter}

<br/>

⏰ {s.time}



</div>


))

}


</div>


}









{/* ================= HEAT ================= */}


{
page==="heat" &&


<div>


<h2 className="text-2xl mb-5">

🔥 Cat Hotspots

</h2>



{
Object.keys(heat).map(zone=>(


<div

key={zone}

className="
bg-slate-900
rounded-xl
p-4
mb-3
"

>


{zones[zone]?.name}


<br/>


{"🐱".repeat(heat[zone])}



</div>


))

}


</div>

}









{/* ================= DIARY ================= */}


{
page==="diary" &&


<div
className="
bg-slate-900
rounded-xl
p-6
"
>


<h2 className="text-2xl">

📖 Moulinette's Diary

</h2>


<p className="mt-4">

Today I explored the campus...
Meow 🐱

</p>



</div>


}









{/* ================= GUESS ================= */}


{
page==="guess" &&

<GuessCat/>

}









{/* ================= RANKING ================= */}



{
page==="ranking" &&


<div
className="
bg-slate-900
rounded-xl
p-6
"
>


<h2 className="text-2xl">

🏆 Ranking

</h2>



<p>

🥇 Test - 250 pts

</p>


<p>

🥈 Test - 180 pts

</p>



</div>


}







<ReportButton />


<GameMenu

page={page}

setPage={setPage}

/>



</div>


);


}