import { createStore } from 'vuex';
import axios from 'axios';

export default createStore({
  state: {
    users: []
  },
  getters: {
    allUsers: state => state.users
  },
  mutations: {
    setUsers(state, users) {
      state.users = users;
    }
  },
  actions: {
    async fetchUsers({ commit }) {
      try {
        const response = await axios.get('https://blogi-36jo.onrender.com'); // Backend API URL
        commit('setUsers', response.data);
      } catch (error) {
        console.error('Error fetching users:', error);
      }
    }
  },
  modules: {}
});
