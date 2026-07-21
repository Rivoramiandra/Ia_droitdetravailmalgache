import { createRouter, createWebHistory } from 'vue-router'

import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import About from '../views/About.vue'

const routes = [
  { path: '/', name: 'home', component: Home, meta: { title: 'Accueil' } },
  { path: '/chat', name: 'chat', component: Chat, meta: { title: 'Chatbot' } },
  { path: '/about', name: 'about', component: About, meta: { title: 'À propos' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · Vue AI` : 'Vue AI'
})

export default router
