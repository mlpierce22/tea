def create_tea_component() -> str:
    return f"""
<script setup>
import Steep from './Steep.vue'
</script>

<template>
    <Steep></Steep>
</template>
"""

def create_steep_component() -> str:
    return f"""
<script setup>
// Remove this import when removing the Brewing component!
import Brewing from './Brewing.vue'
</script>

<template>
    <!-- Replace the Brewing component and this comment with your custom implementation! -->
    <Brewing></Brewing>
</template>

<!-- Put styles below if necessary! -->
<style scoped>
</style>
"""

def create_loading_component() -> str:
    return """
<template>
  <div class="container">
    <div class="title">
      <span class="letter" style="animation-delay: 0s;">B</span>
      <span class="letter" style="animation-delay: 0.1s;">r</span>
      <span class="letter" style="animation-delay: 0.2s;">e</span>
      <span class="letter" style="animation-delay: 0.3s;">w</span>
      <span class="letter" style="animation-delay: 0.4s;">i</span>
      <span class="letter" style="animation-delay: 0.5s;">n</span>
      <span class="letter" style="animation-delay: 0.6s;">g</span>
      <span class="letter" style="animation-delay: 0.7s;">.</span>
      <span class="letter" style="animation-delay: 0.8s;">.</span>
      <span class="letter" style="animation-delay: 0.9s;">.</span>
    </div>
  </div>
</template>

<style>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.title {
  display: flex;
  justify-content: center;
}

.letter {
  font-size: 1.5em;
  margin-bottom: 0.5em;
  display: inline-block;
  animation: bouncing 3s infinite ease-in-out both;
}

@keyframes bouncing {

  0%,
  100% {
    transform: translateY(5px);
  }

  50% {
    transform: translateY(-5px);
  }
}
</style>
"""


