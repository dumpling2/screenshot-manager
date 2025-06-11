<template>
  <div id="app">
    <header class="header">
      <h1>📝 Claude Code Todo App</h1>
      <p>Vue.jsで作成されたタスク管理アプリケーション</p>
    </header>

    <main class="main">
      <div class="todo-input">
        <input 
          v-model="newTodo" 
          @keyup.enter="addTodo"
          placeholder="新しいタスクを入力..."
          class="input"
        >
        <button @click="addTodo" class="add-btn">追加</button>
      </div>

      <div class="todo-list">
        <div 
          v-for="todo in todos" 
          :key="todo.id"
          class="todo-item"
          :class="{ completed: todo.completed }"
        >
          <input 
            type="checkbox" 
            v-model="todo.completed"
            class="checkbox"
          >
          <span class="todo-text">{{ todo.text }}</span>
          <button @click="removeTodo(todo.id)" class="remove-btn">削除</button>
        </div>
      </div>

      <div class="stats">
        <p>完了: {{ completedCount }} / 全体: {{ todos.length }}</p>
      </div>
    </main>

    <footer class="footer">
      <p>Screenshot Managerによる自動テスト対象アプリ</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      newTodo: '',
      todos: [
        { id: 1, text: 'Vue.jsプロジェクトの作成', completed: true },
        { id: 2, text: 'Todoアプリの実装', completed: true },
        { id: 3, text: 'Screenshot Managerでのテスト', completed: false },
        { id: 4, text: 'レポート確認', completed: false }
      ]
    }
  },
  computed: {
    completedCount() {
      return this.todos.filter(todo => todo.completed).length
    }
  },
  methods: {
    addTodo() {
      if (this.newTodo.trim()) {
        this.todos.push({
          id: Date.now(),
          text: this.newTodo,
          completed: false
        })
        this.newTodo = ''
      }
    },
    removeTodo(id) {
      this.todos = this.todos.filter(todo => todo.id !== id)
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Arial', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#app {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  color: white;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2.5em;
  margin-bottom: 10px;
}

.main {
  background: rgba(255, 255, 255, 0.1);
  padding: 30px;
  border-radius: 15px;
  backdrop-filter: blur(10px);
}

.todo-input {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

.input {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
}

.add-btn {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
}

.add-btn:hover {
  background: #45a049;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.todo-item:hover {
  background: rgba(255, 255, 255, 0.3);
}

.todo-item.completed {
  opacity: 0.6;
}

.todo-item.completed .todo-text {
  text-decoration: line-through;
}

.checkbox {
  width: 20px;
  height: 20px;
}

.todo-text {
  flex: 1;
  font-size: 16px;
}

.remove-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.remove-btn:hover {
  background: #da190b;
}

.stats {
  margin-top: 20px;
  text-align: center;
  font-size: 18px;
  font-weight: bold;
}

.footer {
  text-align: center;
  margin-top: 30px;
  opacity: 0.8;
}

@media (max-width: 768px) {
  #app {
    padding: 10px;
  }
  
  .header h1 {
    font-size: 2em;
  }
  
  .todo-input {
    flex-direction: column;
  }
}
</style>