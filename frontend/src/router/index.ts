 import { createRouter, createWebHistory } from "vue-router"
 import IndexView from "@/views/IndexView.vue"
import ChatView from "@/views/ChatView.vue"
import NotFound from "@/views/NotFound.vue"
import AuthView from "@/views/admin/AuthView.vue"
const router = createRouter({
  history: createWebHistory(),
  routes: [
  
    {
      path: "/",
      name: "index",
      component: IndexView,
    },
    {
      path: "/c/:id",
      name: "chat",
      component: ChatView,
    },
     {
      path: "/scai-adm",
      name: "admin",
      component: AuthView,
    },

    {
      path: "/:pathMatch(.*)*",
      name: "not-found",
      component: NotFound,
    },
  ],
})

export default router