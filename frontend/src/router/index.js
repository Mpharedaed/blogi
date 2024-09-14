import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import axios from "axios";

// Define route guard to check authentication status
function requireAuth(to, from, next) {
  const token = sessionStorage.getItem("authToken");

  if (token) {
    // Optionally, you can make a request to validate the token with the backend
    axios
      .post("https://blogi-36jo.onrender.com/api/verify-token", { token })
      .then(() => {
        next(); // Continue to the route if the token is valid
      })
      .catch(() => {
        sessionStorage.removeItem("authToken");
        next("/loginsignup"); // Redirect to login if the token is invalid
      });
  } else {
    next("/loginsignup"); // Redirect to login page if no token
  }
}

// Define routes
const routes = [
  {
    path: "/home",
    name: "home",
    component: HomeView,
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/loginsignup",
    name: "loginsignup",
    component: () => import("../components/LoginSignup.vue"),
  },
  {
    path: "/",
    name: "start",
    component: () =>
      import(/* webpackChunkName: "start" */ "../views/StartView.vue"),
  },
  {
    path: "/postblog",
    name: "postblog",
    component: () => import("../components/PostBlog.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/editblog/:id",
    name: "editblog",
    component: () => import("../components/EditBlog.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/postengage/:id",
    name: "postengage",
    component: () => import("../components/PostEngage.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/readblog/:id",
    name: "readblog",
    component: () => import("../components/ReadBlog.vue"),
  },
  {
    path: "/profile/:username",
    name: "profile",
    component: () => import("../components/UserProfile.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/editprofile",
    name: "editprofile",
    component: () => import("../components/EditProfile.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/searchuser",
    name: "searchuser",
    component: () => import("../components/SearchUser.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/comment/:id",
    name: "commentblog",
    component: () => import("../components/CommentBlog.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/followers",
    name: "followers",
    component: () => import("../components/MyFollowers.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
  {
    path: "/followings",
    name: "followings",
    component: () => import("../components/MyFollowings.vue"),
    beforeEnter: requireAuth, // Protect this route, requires authentication
  },
];

// Create and export router instance
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
