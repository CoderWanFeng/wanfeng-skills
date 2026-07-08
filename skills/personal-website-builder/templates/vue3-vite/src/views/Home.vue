<script setup>
import { categories } from '../data/tools.js'
import ToolCard from '../components/ToolCard.vue'
</script>

<template>
  <div class="container">
    <header class="hero">
      <h1>{{SITE_NAME}}</h1>
      <p class="hero-tagline">{{SITE_DESCRIPTION}}</p>
    </header>

    <div v-for="cat in categories" :key="cat.id" class="category-section">
      <h2 class="category-title">
        <span class="category-icon">{{ cat.icon }}</span>
        {{ cat.name }}
      </h2>
      <div class="tools-grid">
        <ToolCard v-for="tool in cat.tools" :key="tool.name" :tool="tool" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 3rem 0 4rem;
}

.hero h1 {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-tagline {
  font-size: 1.25rem;
  color: var(--color-text-muted);
  max-width: 600px;
  margin: 0 auto;
}

.category-section {
  margin-bottom: 4rem;
}

.category-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.category-icon {
  font-size: 2rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}
</style>