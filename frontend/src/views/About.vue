<script setup>

import {
    Scale,
    BookOpen,
    MessageCircle,
    Search,
    Users,
    Building2,
    UserRound
} from 'lucide-vue-next'



const features = [

    {
        icon: Scale,
        title:'Comprendre vos droits',
        desc:'Accédez facilement aux informations essentielles sur le droit du travail malgache.'
    },


    {
        icon: BookOpen,
        title:'Informations juridiques',
        desc:'Consultez des informations claires concernant les règles et obligations professionnelles.'
    },


    {
        icon: MessageCircle,
        title:'Consultation simple',
        desc:'Posez vos questions et obtenez rapidement des explications adaptées à votre situation.'
    },


    {
        icon: Search,
        title:'Recherche facilitée',
        desc:'Retrouvez facilement les informations relatives au droit du travail.'
    }

]



</script>




<template>


<section class="about">


<div class="about-inner">



<div class="hero-about">


<h1>
    LegalAI
</h1>


<p class="subtitle">
    Votre assistant juridique pour mieux comprendre le droit du travail malgache.
</p>



<p>

    LegalAI est une application qui facilite l'accès
    aux informations juridiques liées au monde du travail.
    Elle accompagne les salariés, employeurs et citoyens
    dans la compréhension de leurs droits et obligations.

</p>


</div>






<h2>
    Découvrez LegalAI
</h2>




<div class="features">


<div
    v-for="item in features"
    :key="item.title"
    class="card"
>


<div class="icon">

    <component 
        :is="item.icon"
        size="32"
    />

</div>




<h3>
    {{item.title}}
</h3>



<p>
    {{item.desc}}
</p>



</div>


</div>








<h2>
    Notre objectif
</h2>



<p class="mission">

    Rendre le droit du travail malgache plus accessible
    grâce à une plateforme simple, rapide et adaptée
    aux besoins des utilisateurs.

</p>







<h2>
    Pour qui ?
</h2>




<div class="users">


<div class="user-card">

    <UserRound size="24"/>

    <span>
        Salariés
    </span>

</div>




<div class="user-card">

    <Building2 size="24"/>

    <span>
        Employeurs
    </span>

</div>





<div class="user-card">

    <Users size="24"/>

    <span>
        Citoyens
    </span>

</div>



</div>







</div>


</section>


</template>







<style scoped>


.about {

    padding:3rem 1.5rem;

    display:flex;

    justify-content:center;

}



.about-inner {

    max-width:1000px;

    width:100%;

}



.hero-about {

    text-align:center;

    margin-bottom:3rem;

}



h1 {

    font-size:3rem;

    color:#f8fafc;

}



.subtitle {

    font-size:1.3rem;

    color:#38bdf8;

    margin:1rem 0;

}



p {

    color:#cbd5e1;

    line-height:1.7;

}



h2 {

    color:#f8fafc;

    margin:2.5rem 0 1.5rem;

}





.features {

    display:grid;

    grid-template-columns:repeat(2,1fr);

    gap:1.2rem;

}





.card {


    background:#0f172a;


    border:1px solid rgba(148,163,184,.15);


    border-radius:18px;


    padding:1.5rem;


    transition:.2s;


}




.card:hover {

    transform:translateY(-5px);

    border-color:#38bdf8;

}




.icon {

    color:#38bdf8;

    margin-bottom:1rem;

}





.card h3 {

    color:#f8fafc;

}





.mission {

    background:#0f172a;

    padding:1.5rem;

    border-radius:18px;

}





.users {

    display:flex;

    gap:1rem;

    flex-wrap:wrap;

}





.user-card {

    display:flex;

    align-items:center;

    gap:10px;


    background:#0f172a;


    color:#cbd5e1;


    padding:.9rem 1.4rem;


    border-radius:14px;


    border:1px solid rgba(148,163,184,.15);


}



.user-card svg {

    color:#38bdf8;

}





@media(max-width:700px){


.features{

    grid-template-columns:1fr;

}



h1{

    font-size:2.2rem;

}


}


</style>