<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { categories } from '../data/tools.js'
import ToolCard from '../components/ToolCard.vue'

const route = useRoute()
const router = useRouter()

const category = computed(() => {
  return categories.find(c => c.id === route.params.id)
})
</script>

<template>
  <div class="container">
    <button class="back-btn" @click="router.push('/')">← 返回首页</button>

    <div v-if="category" class="category-page">
      <h1>
        <span class="icon">{{ category.icon }}</span>
        {{ category.name }}
      </h1>
      <p class="count">共 {{ category.tools.length }} 个工具</p>
      <div class="tools-grid">
        <ToolCard v-for="tool in category.tools" :key="tool.name" :tool="tool" />
      </div>
    </div>

    <div v-else class="not-found">
      <h2>分类不存在</h2>
    </div>
  </div>
</template>

<style scoped>
.back-btn {
  background: none;
  border: 1px solid var(--color-border);
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--color-text);
  margin-bottom: 2rem;
  font-size: 0.9rem;
}

.back-btn:hover {
  background: var(--color-bg-alt);
}

.category-page h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.icon {
  font-size: 2.5rem;
  margin-right: 0.5rem;
}

.count {
  color: var(--color-text-muted);
  margin-bottom: 2rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.not-found {
  text-align: center;
  padding: 4rem 0;
  color: var(--color-text-muted);
}
</style>