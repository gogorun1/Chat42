import type { Dispatch, SetStateAction } from "react";


interface GameMenuProps {

    page: string;

    setPage: Dispatch<SetStateAction<string>>;

}



export default function GameMenu(
{
    page,
    setPage

}: GameMenuProps
){


const menu = [

    {
        id:"map",
        icon:"🗺",
        name:"Map"
    },

    {
        id:"history",
        icon:"🐾",
        name:"History"
    },

    {
        id:"heat",
        icon:"🔥",
        name:"Heat"
    },

    {
        id:"diary",
        icon:"📖",
        name:"Diary"
    },

    {
        id:"guess",
        icon:"🎯",
        name:"Guess"
    },

    {
        id:"ranking",
        icon:"🏆",
        name:"Ranking"
    }

];



return (

<div
className="
fixed
bottom-0
left-0
right-0
bg-slate-950
border-t
border-yellow-400
p-3
"
>


<div
className="
flex
justify-center
gap-3
flex-wrap
"
>


{
menu.map(item=>(


<button

key={item.id}

onClick={()=>setPage(item.id)}

className={`
px-4
py-2
rounded-lg
border
font-mono
transition

${
page===item.id

?

"bg-yellow-400 text-black"

:

"bg-slate-800 text-white hover:bg-slate-700"

}

`}

>


<div className="text-xl">

{item.icon}

</div>


<div className="text-xs">

{item.name}

</div>


</button>


))
}


</div>


</div>


);


}