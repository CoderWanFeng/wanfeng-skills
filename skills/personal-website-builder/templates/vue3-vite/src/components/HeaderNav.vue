<script setup>
import { categories } from '../data/tools.js'
import { RouterLink } from 'vue-router'
</script>

<template>
  <header class="header">
    <div class="container header-inner">
      <RouterLink to="/" class="logo">{{SITE_NAME}}</RouterLink>
      <nav class="nav">
        <RouterLink
          v-for="cat in categories"
          :key="cat.id"
          :to="`/category/${cat.id}`"
          class="nav-link"
        >
          {{ cat.icon }} {{ cat.name }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
  background-color: rgba(255, 255, 255, 0.8);
}

@media (prefers-color-scheme: dark) {
  .header {
    background-color: rgba(15, 23, 42, 0.8);
  }
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  gap: 2rem;
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
}

.logo:hover {
  color: var(--color-primary);
}

.nav {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.nav-link {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius);
  text-decoration: none;
  transition: all 0.15s;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: var(--color-primary);
  background: var(--color-bg-alt);
  text-decoration: none;
}

@media (max-width: 640px) {
  .header-inner {
    flex-direction: column;
    height: auto;
    padding: 1rem 0;
  }

  .nav {
    gap: 0.5rem;
  }
}
</style>