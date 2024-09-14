<template>
  <div class="bd">
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css"
    />
    <div id="popup">
      <!-- Error and Success Messages -->
      <p class="alert alert-danger alert-dismissible fade show" v-if="serror_1">
        {{ serror_1 }}
        <button
          type="button"
          class="btn-close"
          data-bs-dismiss="alert"
          aria-label="Close"
        ></button>
      </p>
      <p class="alert alert-danger alert-dismissible fade show" v-if="serror_2">
        {{ serror_2 }}
        <button
          type="button"
          class="btn-close"
          data-bs-dismiss="alert"
          aria-label="Close"
        ></button>
      </p>
      <p class="alert alert-danger alert-dismissible fade show" v-if="lerror_1">
        {{ lerror_1 }}
        <button
          type="button"
          class="btn-close"
          data-bs-dismiss="alert"
          aria-label="Close"
        ></button>
      </p>
      <p class="alert alert-danger alert-dismissible fade show" v-if="lerror_2">
        {{ lerror_2 }}
        <button
          type="button"
          class="btn-close"
          data-bs-dismiss="alert"
          aria-label="Close"
        ></button>
      </p>
      <p
        class="alert alert-success alert-dismissible fade show"
        role="alert"
        v-if="success"
      >
        {{ success }}
        <button
          type="button"
          class="btn-close"
          data-bs-dismiss="alert"
          aria-label="Close"
        ></button>
      </p>
    </div>

    <div id="main">
      <input class="out" type="checkbox" id="ck" aria-hidden="true" />

      <!-- SIGNUP PAGE -->
      <div class="signup">
        <form ref="sigform" method="post">
          <label class="lb" for="ck" aria-hidden="true">Sign up</label>
          <input
            class="out"
            type="text"
            v-model="signupData.username"
            placeholder="Enter User Name*"
            required
          />
          <input
            class="out"
            type="email"
            v-model="signupData.email"
            placeholder="Enter Email Id*"
            required
          />
          <input
            class="out"
            type="password"
            v-model="signupData.password1"
            placeholder="Enter Password*"
            required
          />
          <input
            class="out"
            type="password"
            v-model="signupData.password2"
            placeholder="Confirm Password*"
            required
          />
          <button
            type="submit"
            class="tk"
            @click.prevent="signup"
          >
            Sign up
          </button>
        </form>
      </div>

      <!-- LOGIN PAGE -->
      <div class="login">
        <form method="post">
          <label class="lb" for="ck" aria-hidden="true">Login</label>
          <input
            class="out"
            type="text"
            v-model="loginData.username"
            placeholder="Enter your Username"
            required
          />
          <input
            class="out"
            type="password"
            v-model="loginData.password"
            placeholder="Password"
            required
          />
          <button
            type="submit"
            class="tk"
            @click.prevent="login"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "LoginSignup",
  data() {
    return {
      signupData: {
        email: "",
        username: "",
        password1: "",
        password2: "",
      },
      loginData: {
        username: "",
        password: "",
      },
      serror_1: "",
      success: "",
      lerror_1: "",
    };
  },
  methods: {
    // Signup Function
    async signup() {
      if (this.signupData.password1 !== this.signupData.password2) {
        this.serror_1 = "Passwords do not match";
        return;
      }
      try {
        await axios.post("https://blogi-36jo.onrender.com/api/user", {
          email: this.signupData.email,
          username: this.signupData.username,
          password1: this.signupData.password1,
        });
        this.success = "Signup successful!";
        this.resetForm();
      } catch (error) {
        this.serror_1 = error.response?.data?.message || "An error occurred!";
      }
    },

    // Login Function
    async login() {
      try {
        const response = await axios.post(
          "https://blogi-36jo.onrender.com/api/login",
          {
            username: this.loginData.username,
            password: this.loginData.password,
          }
        );
        // If login is successful
        this.success = "Login successful!";

        // Store the token in sessionStorage for future API requests
        sessionStorage.setItem("authToken", response.data.token);

        // Redirect to the home page or another route
        this.$router.push("/home");
      } catch (error) {
        // Handle login errors
        this.lerror_1 = error.response?.data?.message || "Login failed!";
      }
    },

    // Reset Form after Signup
    resetForm() {
      this.signupData.email = "";
      this.signupData.username = "";
      this.signupData.password1 = "";
      this.signupData.password2 = "";
    },
  },
};
</script>



<style scoped>
.bd {
  margin: 0;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  font-family: "jost", sans-serif;
  background: url("https://4kwallpapers.com/images/walls/thumbs_3t/14811.jpg") no-repeat center/cover;
}
#main {
  width: 350px;
  height: 550px;
  overflow: hidden;
  background: url("../assets/1.jpg") no-repeat center / cover;
  border-radius: 10px;
  box-shadow: 5px 20px 50px #000;
}
#ck {
  display: none;
}
.signup {
  position: relative;
  width: 100%;
  height: 100%;
}

.lb {
  color: #fff;
  font-size: 2.3em;
  justify-content: center;
  display: flex;
  margin: 60px;
  font-weight: bold;
  cursor: pointer;
  transition: 0.5s ease-in-out;
}

.out {
  width: 75%;
  height: 35px;
  background: #e0dede;
  justify-content: center;
  display: flex;
  margin: 20px auto;
  padding: 10px;
  border: none;
  outline: none;
  border-radius: 5px;
}

.tk {
  width: 60%;
  height: 40px;
  margin: 10px auto;
  display: block;
  color: #fff;
  background: #573b8a;
  font-size: 1em;
  font-weight: bold;
  margin-top: 20px;
  outline: none;
  border: none;
  border-radius: 5px;
  transition: 0.2s ease-in;
  cursor: pointer;
}

.tk:hover {
  background: #6d44b8;
}

.login {
  height: 500px;
  background: #eee;
  border-radius: 60% / 10%;
  transform: translateY(-180px);
  transition: 0.8s ease-in-out;
}

.login label {
  color: #573b8a;
  transform: scale(0.6);
}

#ck:checked ~ .login {
  transform: translateY(-550px);
}

#ck:checked ~ .login label {
  transform: scale(1);
}
#ck:checked ~ .signup label {
  transform: scale(0.6);
}
.login button {
  bottom: 10%;
}

input[type="email"]::placeholder,
input[type="password"]::placeholder,
input[type="text"]::placeholder {
  color: #b5a1a1;
}

#popup {
  top: 0px;
  position: absolute;
  width: 500px;
  text-align: center;
}
</style>
