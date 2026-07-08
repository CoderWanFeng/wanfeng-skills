<script setup>
import HeaderNav from './components/HeaderNav.vue'
</script>

<template>
  <div class="app">
    <HeaderNav />
    <main class="main">
      <router-view />
    </main>
    <footer class="footer">
      <div class="container">
        <p>{{SITE_NAME}} · {{YEAR}}</p>
        <p>Made with Vue 3 + Vite</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main {
  flex: 1;
  padding: 2rem 0;
}

.footer {
  background: var(--color-bg-alt);
  border-top: 1px solid var(--color-border);
  padding: 2rem 0;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.footer p {
  margin: 0.25rem 0;
}
</style>