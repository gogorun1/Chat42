import { useState } from "react";
import { lastSighting } from "../data/cat";


const guessZones = [

    {
        id:"entrance",
        name:"42 Entrance"
    },

    {
        id:"cantine_m1",
        name:"CantiSkate"
    },

    {
        id:"cantine_0",
        name:"Shokudo"
    },

    {
        id:"cantine_1",
        name:"La Piscine"
    },

    {
        id:"f0",
        name:"Floor 0 Room"
    },

    {
        id:"f1",
        name:"Floor 1 Room"
    },

    {
        id:"f2",
        name:"Floor 2 Room"
    },

    {
        id:"f6",
        name:"Floor 6"
    },

    {
        id:"playroom",
        name:"Cafe avant la fin du monde"
    },

    {
        id:"roof2",
        name:"Terrase (2)"
    },

    {
        id:"roof3",
        name:"Terrase (3)"
    },

    {
        id:"stairs",
        name:"Stairs"
    }

];





export default function GuessCat(){


const [selected,setSelected] =
useState("entrance");


const [result,setResult] =
useState("");



const [points,setPoints] =
useState(120);





function guess(){


    // cost 1 point

    if(points < 1){

        setResult(
            "❌ Not enough points"
        );

        return;

    }



    setPoints(
        points-1
    );



    if(selected===lastSighting.zone){


        setPoints(
            points+2
        );


        setResult(
            "🎉 Correct! +3 points"
        );


    }

    else{


        setResult(
            "😿 Wrong location"
        );


    }



}





return (

<div

className="
bg-slate-900
border
border-yellow-400
rounded-xl
p-6
"

>


<h2

className="
text-2xl
text-yellow-400
mb-4
"

>

🎯 Guess Moulinette

</h2>



<p>

⭐ Cost: 1 point

</p>



<p className="mb-5">

🎁 Reward: +3 points

</p>






<select

value={selected}

onChange={
e=>setSelected(e.target.value)
}

className="
w-full
bg-slate-800
p-3
rounded
mb-5
"

>


{
guessZones.map(z=>(


<option

key={z.id}

value={z.id}

>

{z.name}

</option>


))

}


</select>






<button

onClick={guess}

className="
bg-yellow-400
text-black
px-5
py-3
rounded
"

>

🐾 Guess!

</button>




{
result &&

<p

className="
mt-5
text-xl
"

>

{result}

</p>

}



<div

className="
mt-5
text-sm
text-slate-400
"

>

Remaining points:
{" "}
{points}

</div>




</div>


);


}