<script setup>
defineProps({
  tool: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <a :href="tool.url" target="_blank" rel="noopener noreferrer" class="card">
    <h3 class="card-name">{{ tool.name }}</h3>
    <p class="card-desc">{{ tool.desc }}</p>
    <span class="card-link">访问 →</span>
  </a>
</template>

<style scoped>
.card {
  display: block;
  padding: 1.5rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--color-text);
  transition: all 0.2s;
  box-shadow: var(--shadow);
}

.card:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  text-decoration: none;
}

.card-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.card-desc {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.card-link {
  color: var(--color-primary);
  font-size: 0.85rem;
  font-weight: 500;
}
</style>