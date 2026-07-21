<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <section class="hero">

    <div class="hero-inner">


      <p class="eyebrow">
        LegalAI · Assistant juridique malgache
      </p>



      <h1 class="title">
        Votre assistant pour comprendre le droit du travail à Madagascar.
      </h1>




      <p class="subtitle">

        Posez vos questions juridiques et obtenez des réponses
        basées sur le Code du travail malgache.
        LegalAI vous accompagne pour mieux comprendre vos droits,
        obligations et procédures professionnelles.

      </p>





      <div class="cta">


        <RouterLink 
          to="/chat" 
          class="btn primary"
        >
          Commencer une consultation
        </RouterLink>




        <RouterLink 
          to="/about" 
          class="btn ghost"
        >
          Découvrir LegalAI
        </RouterLink>


      </div>



    </div>


  </section>
</template>



<style scoped>
.hero {
  min-height: 72vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem 1.5rem;
}



.hero-inner { 
  max-width: 700px; 
}



.eyebrow {

  text-transform: uppercase;

  letter-spacing: 0.18em;

  font-size: 0.78rem;

  color: #38bdf8;

  margin: 0 0 0.9rem;

  font-weight: 600;

}



.title {

  font-size: clamp(2rem, 5vw, 3.2rem);

  line-height: 1.1;

  margin: 0 0 1rem;

  color: #f8fafc;

  font-weight: 700;

}



.subtitle {

  font-size: 1.05rem;

  line-height: 1.7;

  color: #cbd5e1;

  margin: 0 auto 2rem;

  max-width: 650px;

}



.cta {

  display:flex;

  gap:0.8rem;

  justify-content:center;

  flex-wrap:wrap;

}



.btn {

  padding:0.75rem 1.5rem;

  border-radius:999px;

  font-weight:600;

  font-size:0.95rem;

  text-decoration:none;

  transition:transform .15s, background .2s;

}



.btn.primary {

  background:linear-gradient(135deg,#38bdf8,#0ea5e9);

  color:#0f172a;

}



.btn.primary:hover {

  transform:translateY(-2px);

}



.btn.ghost {

  background:transparent;

  color:#e2e8f0;

  border:1px solid rgba(148,163,184,.35);

}



.btn.ghost:hover {

  background:rgba(148,163,184,.1);

}


</style>