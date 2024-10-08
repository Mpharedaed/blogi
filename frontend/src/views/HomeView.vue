<template>
  <div class="home">
    <!-- NavBar component, passing the username as a prop -->
    <NavBar :username="username"></NavBar>
    <div class="content-area">
      <div class="content">
        <div class="head-nav">
          <a href="#"> Recent Posts </a>
        </div>
        <!-- Display blogs if they are loaded -->
        <div v-if="blogs && blogs.length" class="allposts">
          <div v-for="blog in blogs" :key="blog.id" class="posts">
            <img
              :src="getImageUrl(blog.image)"
              alt="Post Image"
              class="post-image"
            />
            <div class="post-preview">
              <h1>
                <span v-html="blog.title"></span>
              </h1>
              <div class="info" style="position: absolute; font-size: 1.2rem; top: 85px">
                <i id="usr" class="far fa-user" @click="usr(blog.user)">
                  {{ blog.user }}
                </i>
                &nbsp;
                <i id="dt" class="fa fa-calendar">
                  {{ blog.date }}&nbsp;&nbsp;{{ blog.time }}
                </i>
              </div>
              <p class="preview-text">
                <span v-html="blog.preview"></span>
              </p>
              <div class="intr">
                {{ blog.likes }}
                <i class="fa fa-thumbs-up lk" @click="like(blog.id)"></i>
                &nbsp;&nbsp;
                {{ blog.dislikes }}
                <i class="fa fa-thumbs-down lk" @click="unlike(blog.id)"></i>
                &nbsp;&nbsp;
                {{ blog.comments }}
                <i class="fa fa-comment cmnt" @click="comment(blog.id)"></i>
              </div>
              <a href="#" class="btn" @click.prevent="readblog(blog.id)">
                Read More
              </a>
            </div>
          </div>
        </div>
        <!-- Message when there are no blogs -->
        <div v-else class="nof">
          No feeds. Follow some users to see their blogs.
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// Import NavBar component
import NavBar from "@/components/NavBar.vue";
import axios from "axios";

export default {
  name: "HomeView",
  components: {
    NavBar,
  },
  data() {
    return {
      username: null,
      authToken: null,
      error: "",
      success: "",
      blogs: [],
    };
  },
  async created() {
    // Retrieve auth token and username from sessionStorage
    this.authToken = sessionStorage.getItem("authToken");
    this.username = sessionStorage.getItem("username");
    console.log("Auth Token:", this.authToken);
    console.log("Username:", this.username);

    // Check if auth token is present
    if (!this.authToken) {
      alert("Please log in to see your dashboard.");
      console.log("No auth token found. Redirecting to login page.");
      this.$router.push("/");
      return;
    }

    // Fetch blogs from the API
    console.log("Fetching blogs from API...");
    try {
      const response = await axios.get("https://www.dawlatemad.com/api/blog", {
        headers: {
          "Authentication-Token": this.authToken,
        },
      });

      console.log("API response status:", response.status);

      if (response.status !== 200) {
        console.log("API response not OK:", response.statusText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = response.data;
      console.log("Received data from API:", data);

      this.blogs = data.blogs;
      console.log("Blogs data set:", this.blogs);
    } catch (error) {
      console.log("Error fetching blogs:", error);
      this.error = "Failed to load blogs. Please try again later.";
    }
  },
  methods: {
    // Get the full URL for the blog image
    getImageUrl(imageName) {
      return `https://www.dawlatemad.com/assets/blogs/${imageName}`;
    },
    usr(user) {
      console.log("Navigating to user profile:", user);
      this.$router.push(`/profile/${user}`);
    },
    comment(blogId) {
      console.log("Navigating to comments for blog ID:", blogId);
      this.$router.push(`/comment/${blogId}`);
    },
    readblog(blogId) {
      console.log("Navigating to read blog with ID:", blogId);
      this.$router.push(`/readblog/${blogId}`);
    },
    async like(blogId) {
      console.log("Liking blog ID:", blogId);
      try {
        const res = await axios.post(
          `https://www.dawlatemad.com/api/LikeUnlikeAPI`,
          {
            like: true,
            blog: blogId,
            username: this.username,
            is_authenticated: true,
          },
          {
            headers: {
              "Authentication-Token": this.authToken,
            },
          }
        );

        console.log("Like API response status:", res.status);

        if (res.status === 200) {
          console.log("Successfully liked blog.");
          // Update the likes count locally or refresh the data
          this.refreshBlogs();
        } else {
          console.log("Error liking blog:", res.statusText);
        }
      } catch (error) {
        console.log("Error in like method:", error);
      }
    },
    async unlike(blogId) {
      console.log("Unliking blog ID:", blogId);
      try {
        const res = await axios.post(
          `https://www.dawlatemad.com/api/LikeUnlikeAPI`,
          {
            like: false,
            blog: blogId,
            username: this.username,
            is_authenticated: true,
          },
          {
            headers: {
              "Authentication-Token": this.authToken,
            },
          }
        );

        console.log("Unlike API response status:", res.status);

        if (res.status === 200) {
          console.log("Successfully unliked blog.");
          // Update the dislikes count locally or refresh the data
          this.refreshBlogs();
        } else {
          console.log("Error unliking blog:", res.statusText);
        }
      } catch (error) {
        console.log("Error in unlike method:", error);
      }
    },
    async refreshBlogs() {
      // Fetch the blogs again to update the likes/dislikes counts
      try {
        const response = await axios.get("https://www.dawlatemad.com/api/blog", {
          headers: {
            "Authentication-Token": this.authToken,
          },
        });

        const data = response.data;
        this.blogs = data.blogs;
      } catch (error) {
        console.log("Error refreshing blogs:", error);
      }
    },
  },
};
</script>


<style>
/* @import url("https://fonts.googleapis.com/css2?family=Rubik+Pixels&display=swap"); */
/* @import url("https://fonts.googleapis.com/css2?family=Righteous&display=swap"); */
@import url("https://fonts.googleapis.com/css2?family=Rubik+Gemstones&display=swap");
.content-area {
  background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)),
    url("../assets/s2.png") no-repeat center/cover;
  display: flex;
  border: 1px solid blue;
  min-height: 91vh;
  position: relative;
  overflow: auto;
}

.content {
  display: flex;
  flex-direction: column;
  flex-wrap: wrap;
  width: 90%;
  margin: 30px auto 30px;
  align-items: center;
  position: relative;
  min-height: 75vh;
}

.head-nav {
  position: absolute;
  top: -24px;
  width: 100%;
  height: 80px;
  /* margin: 20px; */
  /* margin: 10px; */
  /* overflow: hidden; */
  display: inline-block;
  /* border: 1px solid gold; */
}
.head-nav a {
  height: 50px;
  font-size: 2rem;
  /* font-weight: bold; */
  font-family: "Rubik Gemstones", cursive;
  /* font-family: "Rubik Pixels", cursive; */
  /* font-family: "Righteous", cursive; */
  margin: 15px;
  padding: 10px;
  color: rgb(255, 255, 255);
  display: inline-block;
  text-decoration: none;
  /* border: 2px solid black; */
  box-shadow: 2px 2px 4px 4px gray;
  /* background: rgb(233, 233, 233); */
  background: transparent;
  cursor: pointer;
  /* float: left; */
}
.head-nav a:hover {
  /* background: wheat; */
  box-shadow: 3px 3px 5px 5px rgb(255, 233, 137);
  transition: 0.5s;
}
/* .rp {
  display: ;
  left: 0px;
} */

.nof {
  text-align: center;
  /* border: 1px solid red; */
  color: #ffffff;
  top: 230px;
  position: absolute;
  width: 800px;
  right: 250px;
  font-family: "Rubik Bubbles", cursive;
  font-size: 2rem;
  -webkit-text-stroke-width: 1px;
  -webkit-text-stroke-color: #00ebfc;
  background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5));
}
.allposts {
  /* background: url("../static/pp12.jpg") no-repeat center/cover; */
  background: transparent;
  position: absolute;
  top: 44px;
  width: 97%;
  min-height: 700px;
}

.posts {
  /* left: 20px; */
  /* position: relative; */
  overflow: hidden;
  display: flex;
  flex-direction: row;
  margin: 30px 0;
  width: 100%;
  max-height: 270px;
  border-radius: 0px;
  background: white;
  /* border: 1px solid red; */
  box-shadow: 5px 5px 15px 6px #8706ff;
}

.posts:hover {
  box-shadow: 0px 5px 15px 6px rgb(255, 233, 143);
}

.posts img {
  width: 40%;
  height: 270px;
  float: left;
  margin: 0%;
  /* border: 1px solid yellowgreen; */
}

.post-preview {
  width: 60%;
  padding: 0px;
  float: right;
  margin-left: 5px;
  /* border: 1px solid red; */
  position: relative;
  height: 270px;
}
.post-preview h1 {
  /* border: 1px solid red; */
  display: absolute;
  top: 0px;
  max-height: 80px;
  overflow: hidden;
  margin: 0px;
  text-align: left;
}
.preview-text {
  position: absolute;
  /* border: 1px solid red; */
  top: 100px;
  max-height: 100px;
  max-width: 870px;
  overflow: hidden;
}
.intr {
  position: absolute;
  font-size: 1.7rem;
  bottom: 0px;
}
.intr a {
  color: gray;
  margin-left: 4px;
}
/* #lk {
  color: red;
} */
.cmnt {
  color: gray;
  cursor: pointer;
}
.lk {
  color: gray;
}
.lk:hover {
  color: red;
  cursor: pointer;
}

.cmnt:hover {
  color: rgb(63, 62, 62);
}
#usr {
  color: blue;
  font-weight: bold;
}
#usr:hover {
  color: rgb(72, 17, 201);
  cursor: pointer;
}

.btn {
  padding: 0.5rem 1rem;

  background: transparent;
  color: rgb(116, 20, 196);
  border: 1px solid transparent;
  border-radius: 0.25rem;
  text-decoration: none;
  cursor: pointer;
  position: absolute;
  right: 7px;
  bottom: 7px;
  font-weight: 600;
  font-size: 1.15rem;
  box-shadow: 1.2px 1.2px 1.2px 1.2px grey;
}

.btn:hover {
  /* background: #4a1e85; */
  background: #6939a7;
  box-shadow: 2px 2px 1.8px 2px rgb(80, 79, 79);
  transition: 0.5s;
  color: white;
}
</style>
